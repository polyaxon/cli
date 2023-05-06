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

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from clipped.utils.lists import to_list
from clipped.utils.sanitizers import sanitize_string_dict
from clipped.utils.strings import slugify

from polyaxon import pkg, settings
from polyaxon.api import VERSION_V1
from polyaxon.auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.containers.names import SIDECAR_PREFIX
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.annotations import get_connection_annotations
from polyaxon.k8s.converter.common.containers import (
    ensure_container_name,
    sanitize_container,
)
from polyaxon.k8s.converter.common.env_vars import (
    get_base_env_vars,
    get_env_var,
    get_proxy_env_vars,
    get_service_env_vars,
)
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
from polyaxon.k8s.replica import ReplicaSpec
from polyaxon.polyflow import V1Environment, V1Init, V1Plugins
from polyaxon.runner.converter import BaseConverter as _BaseConverter
from polyaxon.schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1TensorboardType,
)
from polyaxon.services.headers import PolyaxonServiceHeaders


class BaseConverter(_BaseConverter):
    GROUP: Optional[str] = None
    API_VERSION: Optional[str] = None
    PLURAL: Optional[str] = None
    K8S_ANNOTATIONS_KIND: Optional[str] = None
    K8S_LABELS_COMPONENT: Optional[str] = None
    K8S_LABELS_PART_OF: Optional[str] = None

    def is_valid(self):
        super().is_valid()
        if not self.GROUP:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid GROUP"
            )
        if not self.API_VERSION:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid API_VERSION"
            )
        if not self.PLURAL:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid PLURAL"
            )
        if not self.K8S_ANNOTATIONS_KIND:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid K8S_ANNOTATIONS_KIND"
            )
        if not self.K8S_LABELS_COMPONENT:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid K8S_LABELS_COMPONENT"
            )
        if not self.K8S_LABELS_PART_OF:
            raise PolyaxonConverterError(
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
    ) -> Dict:
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

    def get_labels(self, version: str, labels: Dict) -> Dict:
        labels = labels or {}
        labels = copy.copy(labels)
        labels.update(self.get_recommended_labels(version=version))
        return sanitize_string_dict(labels)

    def _get_service_env_vars(
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
            namespace=self.namespace,
            resource_name=self.resource_name,
            use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
        )

    @staticmethod
    def _get_base_env_vars(
        namespace: str,
        resource_name: str,
        use_proxy_env_vars_use_in_ops: bool,
        log_level: Optional[str] = None,
    ) -> List[k8s_schemas.V1EnvVar]:
        return get_base_env_vars(
            namespace=namespace,
            resource_name=resource_name,
            use_proxy_env_vars_use_in_ops=use_proxy_env_vars_use_in_ops,
            log_level=log_level,
        )

    @staticmethod
    def _get_env_var(name: str, value: Any) -> k8s_schemas.V1EnvVar:
        raise get_env_var(name=name, value=value)

    @staticmethod
    def _get_proxy_env_vars(
        use_proxy_env_vars_use_in_ops: bool,
    ) -> List[k8s_schemas.V1EnvVar]:
        return get_proxy_env_vars(
            use_proxy_env_vars_use_in_ops=use_proxy_env_vars_use_in_ops
        )

    @staticmethod
    def _get_main_container(
        container_id: str,
        main_container: k8s_schemas.V1Container,
        plugins: V1Plugins,
        artifacts_store: Optional[V1Connection],
        init: Optional[List[V1Init]],
        connections: Optional[List[str]],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        run_path: Optional[str],
        kv_env_vars: List[List] = None,
        env: List[k8s_schemas.V1EnvVar] = None,
        ports: List[int] = None,
    ) -> k8s_schemas.V1Container:
        return get_main_container(
            container_id=container_id,
            main_container=main_container,
            plugins=plugins,
            artifacts_store=artifacts_store,
            init=init,
            connections=connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            run_path=run_path,
            kv_env_vars=kv_env_vars,
            env=env,
            ports=ports,
        )

    @staticmethod
    def _get_custom_init_container(
        connection: V1Connection,
        plugins: V1Plugins,
        container: Optional[k8s_schemas.V1Container],
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ):
        return get_custom_init_container(
            connection=connection,
            plugins=plugins,
            container=container,
            env=env,
            mount_path=mount_path,
        )

    @staticmethod
    def _get_dockerfile_init_container(
        polyaxon_init: V1PolyaxonInitContainer,
        dockerfile_args: V1DockerfileType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[k8s_schemas.V1Container] = None,
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ):
        return get_dockerfile_init_container(
            polyaxon_init=polyaxon_init,
            dockerfile_args=dockerfile_args,
            plugins=plugins,
            run_path=run_path,
            run_instance=run_instance,
            container=container,
            env=env,
            mount_path=mount_path,
        )

    @staticmethod
    def _get_file_init_container(
        polyaxon_init: V1PolyaxonInitContainer,
        file_args: V1FileType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[k8s_schemas.V1Container] = None,
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ):
        return get_file_init_container(
            polyaxon_init=polyaxon_init,
            file_args=file_args,
            plugins=plugins,
            run_path=run_path,
            run_instance=run_instance,
            container=container,
            env=env,
            mount_path=mount_path,
        )

    @staticmethod
    def _get_git_init_container(
        polyaxon_init: V1PolyaxonInitContainer,
        connection: V1Connection,
        plugins: V1Plugins,
        container: Optional[k8s_schemas.V1Container] = None,
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
        track: bool = False,
    ):
        return get_git_init_container(
            polyaxon_init=polyaxon_init,
            connection=connection,
            plugins=plugins,
            container=container,
            env=env,
            mount_path=mount_path,
            track=track,
        )

    @staticmethod
    def _get_store_container(
        polyaxon_init: V1PolyaxonInitContainer,
        connection: V1Connection,
        artifacts: V1ArtifactsType,
        paths: Union[List[str], List[Tuple[str, str]]],
        container: Optional[k8s_schemas.V1Container] = None,
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
        is_default_artifacts_store: bool = False,
    ):
        return get_store_container(
            polyaxon_init=polyaxon_init,
            connection=connection,
            artifacts=artifacts,
            paths=paths,
            container=container,
            env=env,
            mount_path=mount_path,
            is_default_artifacts_store=is_default_artifacts_store,
        )

    @staticmethod
    def _get_tensorboard_init_container(
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        tb_args: V1TensorboardType,
        plugins: V1Plugins,
        run_instance: str,
        container: Optional[k8s_schemas.V1Container] = None,
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ):
        return get_tensorboard_init_container(
            polyaxon_init=polyaxon_init,
            artifacts_store=artifacts_store,
            tb_args=tb_args,
            plugins=plugins,
            run_instance=run_instance,
            container=container,
            env=env,
            mount_path=mount_path,
        )

    @staticmethod
    def _get_auth_context_container(
        polyaxon_init: V1PolyaxonInitContainer,
        env: Optional[List[k8s_schemas.V1EnvVar]] = None,
    ) -> k8s_schemas.V1Container:
        return get_auth_context_container(polyaxon_init=polyaxon_init, env=env)

    @staticmethod
    def _get_artifacts_path_container(
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        run_path: str,
        auto_resume: bool,
        env: Optional[List[k8s_schemas.V1EnvVar]] = None,
    ) -> k8s_schemas.V1Container:
        return get_artifacts_path_container(
            polyaxon_init=polyaxon_init,
            artifacts_store=artifacts_store,
            run_path=run_path,
            auto_resume=auto_resume,
            env=env,
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
        return containers

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
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
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
        init_containers = [sanitize_container(c) for c in init_containers]

        sidecar_containers = self.get_sidecar_containers(
            polyaxon_sidecar=self.polyaxon_sidecar,
            plugins=plugins,
            artifacts_store=artifacts_store,
            sidecar_containers=sidecars,
            log_level=plugins.log_level,
        )
        sidecar_containers = [sanitize_container(c) for c in sidecar_containers]

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
