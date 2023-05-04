#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy

from typing import Any, Dict, Iterable, List, Optional

from clipped.utils.http import clean_host
from clipped.utils.lists import to_list
from clipped.utils.sanitizers import sanitize_string_dict
from clipped.utils.strings import slugify
from vents.connections.connection_schema import patch_git

from polyaxon import pkg, settings
from polyaxon.api import VERSION_V1
from polyaxon.auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon.connections import V1Connection, V1ConnectionKind, V1K8sResource
from polyaxon.containers.names import INIT_PREFIX, SIDECAR_PREFIX
from polyaxon.env_vars.keys import EV_KEYS_LOG_LEVEL, EV_KEYS_NO_API
from polyaxon.exceptions import PolypodException
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.annotations import get_connection_annotations
from polyaxon.k8s.containers import ensure_container_name, sanitize_container
from polyaxon.k8s.converter.init.artifacts import get_artifacts_path_container
from polyaxon.k8s.converter.init.auth import get_auth_context_container
from polyaxon.k8s.converter.init.custom import get_custom_init_container
from polyaxon.k8s.converter.init.dockerfile import get_dockerfile_init_container
from polyaxon.k8s.converter.init.file import get_file_init_container
from polyaxon.k8s.converter.init.git import get_git_init_container
from polyaxon.k8s.converter.init.store import get_store_container
from polyaxon.k8s.converter.init.tensorboard import get_tensorboard_init_container
from polyaxon.k8s.converter.main.container import get_main_container
from polyaxon.k8s.converter.pod.volumes import get_pod_volumes
from polyaxon.k8s.converter.sidecar.container import get_sidecar_container
from polyaxon.k8s.env_vars import (
    get_base_env_vars,
    get_env_var,
    get_proxy_env_vars,
    get_service_env_vars,
)
from polyaxon.k8s.mounts import get_mounts
from polyaxon.k8s.replica import ReplicaSpec
from polyaxon.polyflow import V1Environment, V1Init, V1Plugins
from polyaxon.runner.converter import BaseConverter as _BaseConverter
from polyaxon.services.auth import AuthenticationTypes
from polyaxon.services.headers import PolyaxonServiceHeaders
from polyaxon.services.values import PolyaxonServices


class BaseConverter(_BaseConverter):
    GROUP = None
    API_VERSION = None
    PLURAL = None
    K8S_ANNOTATIONS_KIND = None
    K8S_LABELS_COMPONENT = None
    K8S_LABELS_PART_OF = None

    def __init__(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        run_path: Optional[str] = None,
        namespace: str = "default",
        internal_auth: bool = False,
        polyaxon_sidecar: V1PolyaxonSidecarContainer = None,
        polyaxon_init: V1PolyaxonInitContainer = None,
        base_env_vars: bool = False,
    ):
        super().__init__(
            owner_name=owner_name,
            project_name=project_name,
            run_name=run_name,
            run_uuid=run_uuid,
            run_path=run_path,
            namespace=namespace,
            internal_auth=internal_auth,
            base_env_vars=base_env_vars,
        )
        self.polyaxon_sidecar = polyaxon_sidecar
        self.polyaxon_init = polyaxon_init

    def is_valid(self):
        super().is_valid()
        if not self.GROUP:
            raise PolypodException(
                "Please make sure that a converter subclass has a valid GROUP"
            )
        if not self.API_VERSION:
            raise PolypodException(
                "Please make sure that a converter subclass has a valid API_VERSION"
            )
        if not self.PLURAL:
            raise PolypodException(
                "Please make sure that a converter subclass has a valid PLURAL"
            )
        if not self.K8S_ANNOTATIONS_KIND:
            raise PolypodException(
                "Please make sure that a converter subclass has a valid K8S_ANNOTATIONS_KIND"
            )
        if not self.K8S_LABELS_COMPONENT:
            raise PolypodException(
                "Please make sure that a converter subclass has a valid K8S_LABELS_COMPONENT"
            )
        if not self.K8S_LABELS_PART_OF:
            raise PolypodException(
                "Please make sure that a converter subclass has a valid K8S_LABELS_PART_OF"
            )

    def get_recommended_labels(self, version: str):
        return {
            "app.kubernetes.io/name": slugify(
                self.run_name[:63] if self.run_name else self.run_name
            ),
            "app.kubernetes.io/instance": self.run_uuid,
            "app.kubernetes.io/version": version,
            "app.kubernetes.io/part-of": self.K8S_LABELS_PART_OF,
            "app.kubernetes.io/component": self.K8S_LABELS_COMPONENT,
            "app.kubernetes.io/managed-by": "polyaxon",
        }

    @property
    def annotations(self):
        return {
            "operation.polyaxon.com/name": self.run_name,
            "operation.polyaxon.com/owner": self.owner_name,
            "operation.polyaxon.com/project": self.project_name,
            "operation.polyaxon.com/kind": self.K8S_ANNOTATIONS_KIND,
        }

    def get_annotations(
        self,
        annotations: Dict,
        artifacts_store: Optional[V1Connection],
        init_connections: Optional[List[V1Init]],
        connections: List[str],
        connection_by_names: Optional[Dict[str, V1Connection]],
    ):
        annotations = annotations or {}
        annotations = copy.copy(annotations)
        connections_annotations = get_connection_annotations(
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            connections=connections,
            connection_by_names=connection_by_names,
        )
        connections_annotations = connections_annotations or {}
        annotations.update(connections_annotations)
        annotations.update(self.annotations)
        return sanitize_string_dict(annotations)

    def get_labels(self, version: str, labels: Dict):
        labels = labels or {}
        labels = copy.copy(labels)
        labels.update(self.get_recommended_labels(version=version))
        return sanitize_string_dict(labels)

    def get_service_env_vars(
        self,
        service_header: str,
        header: Optional[str] = None,
        include_secret_key: bool = False,
        include_internal_token: bool = False,
        include_agent_token: bool = False,
        authentication_type: Optional[str] = None,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> List[k8s_schemas.V1EnvVar]:
        header = header or PolyaxonServiceHeaders.SERVICE
        return get_service_env_vars(
            header=header,
            service_header=service_header,
            authentication_type=authentication_type,
            include_secret_key=include_secret_key,
            include_internal_token=include_internal_token,
            include_agent_token=include_agent_token,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            api_host=self.get_api_host(external_host),
            log_level=log_level,
            api_version=VERSION_V1,
            run_instance=self.run_instance,
            use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
        )

    def get_main_env_vars(
        self, external_host: bool = False, log_level: Optional[str] = None, **kwargs
    ) -> Optional[List[k8s_schemas.V1EnvVar]]:
        if self.base_env_vars:
            return get_base_env_vars(
                settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops, log_level=log_level
            )
        return self.get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=external_host,
            log_level=log_level,
        )

    def get_polyaxon_sidecar_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[k8s_schemas.V1EnvVar]]:
        if not self.base_env_vars:
            return self.get_service_env_vars(
                service_header=PolyaxonServices.SIDECAR,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env += [get_env_var(name=EV_KEYS_NO_API, value=True)]
        if log_level:
            env += [get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level)]
        proxy_env = get_proxy_env_vars(
            settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
        )
        if proxy_env:
            env += proxy_env
        return env

    def get_auth_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[k8s_schemas.V1EnvVar]]:
        if self.base_env_vars:
            return None
        return self.get_service_env_vars(
            service_header=PolyaxonServices.INITIALIZER,
            include_internal_token=self.internal_auth,
            include_agent_token=not self.internal_auth,
            authentication_type=(
                AuthenticationTypes.INTERNAL_TOKEN
                if self.internal_auth
                else AuthenticationTypes.TOKEN
            ),
            header=(
                PolyaxonServiceHeaders.INTERNAL
                if self.internal_auth
                else PolyaxonServiceHeaders.SERVICE
            ),
            external_host=external_host,
            log_level=log_level,
        )

    def get_init_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[k8s_schemas.V1EnvVar]]:
        if not self.base_env_vars:
            return self.get_service_env_vars(
                service_header=PolyaxonServices.INITIALIZER,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env.append(get_env_var(name=EV_KEYS_NO_API, value=True))
        if log_level:
            env.append(get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level))
        proxy_env = get_proxy_env_vars(
            settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
        )
        if proxy_env:
            env += proxy_env
        return env

    def get_main_container(
        self,
        main_container: k8s_schemas.V1Container,
        plugins: V1Plugins,
        artifacts_store: V1Connection,
        connections: List[str],
        init_connections: Optional[List[V1Init]],
        connection_by_names: Dict[str, V1Connection],
        log_level: str,
        secrets: Optional[Iterable[V1K8sResource]],
        config_maps: Optional[Iterable[V1K8sResource]],
        kv_env_vars: List[List] = None,
        ports: List[int] = None,
    ) -> k8s_schemas.V1Container:
        env = self.get_main_env_vars(
            external_host=plugins.external_host if plugins else False,
            log_level=log_level,
        )
        volume_mounts = get_mounts(
            use_auth_context=plugins.auth,
            use_artifacts_context=False,  # Main container has a check and handling for this
            use_docker_context=plugins.docker,
            use_shm_context=plugins.shm,
        )

        return get_main_container(
            container_id=self.MAIN_CONTAINER_ID,
            main_container=main_container,
            volume_mounts=volume_mounts,
            plugins=plugins,
            artifacts_store=artifacts_store,
            connections=connections,
            init=init_connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            kv_env_vars=kv_env_vars,
            env=env,
            ports=ports,
            run_path=self.run_path,
        )

    def get_sidecar_containers(
        self,
        polyaxon_sidecar: V1PolyaxonSidecarContainer,
        plugins: V1Plugins,
        artifacts_store: V1Connection,
        sidecar_containers: List[k8s_schemas.V1Container],
        log_level: Optional[str] = None,
    ) -> List[k8s_schemas.V1Container]:
        sidecar_containers = [
            ensure_container_name(container=c, prefix=SIDECAR_PREFIX)
            for c in to_list(sidecar_containers, check_none=True)
        ]
        polyaxon_sidecar_container = get_sidecar_container(
            container_id=self.MAIN_CONTAINER_ID,
            polyaxon_sidecar=polyaxon_sidecar,
            env=self.get_polyaxon_sidecar_service_env_vars(
                external_host=plugins.external_host if plugins else False,
                log_level=log_level,
            ),
            artifacts_store=artifacts_store,
            plugins=plugins,
            run_path=self.run_path,
        )
        containers = to_list(polyaxon_sidecar_container, check_none=True)
        containers += sidecar_containers
        return [sanitize_container(c) for c in containers]

    def handle_init_connections(
        self,
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        init_connections: List[V1Init],
        connection_by_names: Dict[str, V1Connection],
        plugins: V1Plugins,
        log_level: Optional[str] = None,
    ) -> List[k8s_schemas.V1Container]:
        containers = []
        external_host = plugins.external_host if plugins else False

        # Prepare connections that Polyaxon can init automatically
        for init_connection in init_connections:
            if init_connection.connection:
                connection_spec = connection_by_names.get(init_connection.connection)
                # Handling ssh with git
                if (
                    V1ConnectionKind.is_ssh(connection_spec.kind)
                    and init_connection.git
                ):
                    patch_git(connection_spec.schema_, init_connection.git)
                    containers.append(
                        get_git_init_container(
                            polyaxon_init=polyaxon_init,
                            connection=connection_spec,
                            container=init_connection.container,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                            track=True,
                        )
                    )
                elif V1ConnectionKind.is_git(connection_spec.kind):
                    if init_connection.git:  # Update the default schema
                        connection_spec.schema_.patch(init_connection.git)
                    containers.append(
                        get_git_init_container(
                            polyaxon_init=polyaxon_init,
                            connection=connection_spec,
                            container=init_connection.container,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                            track=True,
                        )
                    )
                elif V1ConnectionKind.is_artifact(connection_spec.kind):
                    containers.append(
                        get_store_container(
                            polyaxon_init=polyaxon_init,
                            connection=connection_spec,
                            artifacts=init_connection.artifacts,
                            paths=init_connection.paths,
                            container=init_connection.container,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            is_default_artifacts_store=artifacts_store
                            and init_connection.connection == artifacts_store.name,
                        )
                    )
                else:
                    containers.append(
                        get_custom_init_container(
                            connection=connection_spec,
                            container=init_connection.container,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                        )
                    )
            else:
                # artifacts init without connection should default to the artifactsStore
                if init_connection.artifacts or init_connection.paths:
                    containers.append(
                        get_store_container(
                            polyaxon_init=polyaxon_init,
                            connection=artifacts_store,
                            artifacts=init_connection.artifacts,
                            paths=init_connection.paths,
                            container=init_connection.container,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            is_default_artifacts_store=True,
                        )
                    )
                # git init without connection
                if init_connection.git:
                    git_name = init_connection.git.get_name()
                    containers.append(
                        get_git_init_container(
                            polyaxon_init=polyaxon_init,
                            connection=V1Connection(
                                name=git_name,
                                kind=V1ConnectionKind.GIT,
                                schema_=init_connection.git,
                                secret=None,
                            ),
                            container=init_connection.container,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                            track=False,
                        )
                    )
                # Dockerfile initialization
                if init_connection.dockerfile:
                    containers.append(
                        get_dockerfile_init_container(
                            polyaxon_init=polyaxon_init,
                            dockerfile_args=init_connection.dockerfile,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            container=init_connection.container,
                            plugins=plugins,
                            run_path=self.run_path,
                            run_instance=self.run_instance,
                        )
                    )
                # File initialization
                if init_connection.file:
                    containers.append(
                        get_file_init_container(
                            polyaxon_init=polyaxon_init,
                            file_args=init_connection.file,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            container=init_connection.container,
                            plugins=plugins,
                            run_path=self.run_path,
                            run_instance=self.run_instance,
                        )
                    )
                # Tensorboard initialization
                if init_connection.tensorboard:
                    containers.append(
                        get_tensorboard_init_container(
                            polyaxon_init=polyaxon_init,
                            artifacts_store=artifacts_store,
                            tb_args=init_connection.tensorboard,
                            env=self.get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            container=init_connection.container,
                            plugins=plugins,
                            run_instance=self.run_instance,
                        )
                    )

        return containers

    def get_init_containers(
        self,
        polyaxon_init: V1PolyaxonInitContainer,
        plugins: V1Plugins,
        artifacts_store: V1Connection,
        init_connections: List[V1Init],
        init_containers: List[k8s_schemas.V1Container],
        connection_by_names: Dict[str, V1Connection],
        log_level: Optional[str] = None,
    ) -> List[k8s_schemas.V1Container]:
        init_containers = [
            ensure_container_name(container=c, prefix=INIT_PREFIX)
            for c in to_list(init_containers, check_none=True)
        ]
        init_connections = to_list(init_connections, check_none=True)
        containers = []

        # Add auth context
        if plugins and plugins.auth:
            containers.append(
                get_auth_context_container(
                    polyaxon_init=polyaxon_init,
                    env=self.get_auth_service_env_vars(
                        external_host=plugins.external_host
                    ),
                )
            )

        # Add outputs
        if plugins and plugins.collect_artifacts:
            containers += to_list(
                get_artifacts_path_container(
                    polyaxon_init=polyaxon_init,
                    artifacts_store=artifacts_store,
                    run_path=self.run_path,
                    auto_resume=plugins.auto_resume,
                    env=get_proxy_env_vars(
                        settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
                    ),
                ),
                check_none=True,
            )

        containers += self.handle_init_connections(
            polyaxon_init=polyaxon_init,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
            plugins=plugins,
            log_level=log_level,
        )
        init_containers = containers + init_containers
        return [sanitize_container(c) for c in init_containers]

    def filter_containers_from_init(
        self, init: List[V1Init]
    ) -> List[k8s_schemas.V1Container]:
        return [i.container for i in init if not i.has_connection()]

    def filter_connections_from_init(self, init: List[V1Init]) -> List[V1Init]:
        return [i for i in init if i.has_connection()]

    def get_replica_resource(
        self,
        environment: V1Environment,
        plugins: V1Plugins,
        volumes: List[k8s_schemas.V1Volume],
        init: List[V1Init],
        sidecars: List[k8s_schemas.V1Container],
        container: k8s_schemas.V1Container,
        artifacts_store: V1Connection,
        connections: List[str],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1K8sResource]],
        config_maps: Optional[Iterable[V1K8sResource]],
        kv_env_vars: List[List],
        default_sa: Optional[str] = None,
        ports: List[int] = None,
        num_replicas: Optional[int] = None,
    ) -> ReplicaSpec:
        volumes = volumes or []
        init = init or []
        sidecars = sidecars or []
        connections = connections or []
        environment = environment or V1Environment()
        environment.service_account_name = (
            environment.service_account_name
            or default_sa
            or settings.AGENT_CONFIG.runs_sa
        )

        init_connections = self.filter_connections_from_init(init=init)

        volumes = get_pod_volumes(
            plugins=plugins,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            connections=connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            volumes=volumes,
        )

        init_containers = self.get_init_containers(
            polyaxon_init=self.polyaxon_init,
            plugins=plugins,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            init_containers=self.filter_containers_from_init(init=init),
            connection_by_names=connection_by_names,
            log_level=plugins.log_level,
        )

        sidecar_containers = self.get_sidecar_containers(
            polyaxon_sidecar=self.polyaxon_sidecar,
            plugins=plugins,
            artifacts_store=artifacts_store,
            sidecar_containers=sidecars,
            log_level=plugins.log_level,
        )

        main_container = self.get_main_container(
            main_container=container,
            plugins=plugins,
            artifacts_store=artifacts_store,
            connections=connections,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
            log_level=plugins.log_level,
            secrets=secrets,
            config_maps=config_maps,
            ports=ports,
            kv_env_vars=kv_env_vars,
        )

        labels = self.get_labels(version=pkg.VERSION, labels=environment.labels)
        annotations = self.get_annotations(
            annotations=environment.annotations,
            artifacts_store=artifacts_store,
            connections=connections,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
        )
        return ReplicaSpec(
            volumes=volumes,
            init_containers=init_containers,
            sidecar_containers=sidecar_containers,
            main_container=main_container,
            labels=labels,
            annotations=annotations,
            environment=environment,
            num_replicas=num_replicas,
        )

    def get_resource(self, **kwargs) -> Dict:
        raise NotImplementedError
