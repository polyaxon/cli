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

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from clipped.utils.http import clean_host
from clipped.utils.lists import to_list
from vents.connections.connection_schema import patch_git

from polyaxon import settings
from polyaxon.auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon.connections import V1Connection, V1ConnectionKind, V1ConnectionResource
from polyaxon.containers.names import INIT_PREFIX
from polyaxon.docker import docker_types
from polyaxon.env_vars.keys import EV_KEYS_LOG_LEVEL, EV_KEYS_NO_API
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.containers import ensure_container_name
from polyaxon.polyflow import V1Init, V1Plugins
from polyaxon.schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1TensorboardType,
)
from polyaxon.services.auth import AuthenticationTypes
from polyaxon.services.headers import PolyaxonServiceHeaders
from polyaxon.services.values import PolyaxonServices
from polyaxon.utils.fqn_utils import get_resource_name, get_run_instance
from polyaxon.utils.host_utils import get_api_host

EnvVar = Union[k8s_schemas.V1EnvVar, docker_types.V1EnvVar]
Container = Union[k8s_schemas.V1Container, docker_types.V1Container]
ResourceSpec = Union[Dict, List[str]]


class BaseConverter:
    SPEC_KIND: Optional[str] = None
    MAIN_CONTAINER_ID: Optional[str] = None

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
        self.is_valid()
        self.owner_name = owner_name
        self.project_name = project_name
        self.run_name = run_name
        self.run_uuid = run_uuid
        self.run_path = run_path or self.run_uuid
        self.resource_name = self.get_resource_name()
        self.run_instance = self.get_instance()
        self.namespace = namespace
        self.internal_auth = internal_auth
        self.base_env_vars = base_env_vars
        self.polyaxon_sidecar = polyaxon_sidecar
        self.polyaxon_init = polyaxon_init

    def get_instance(self) -> str:
        return get_run_instance(
            owner=self.owner_name, project=self.project_name, run_uuid=self.run_uuid
        )

    def get_resource_name(self) -> str:
        return get_resource_name(self.run_uuid)

    def is_valid(self):
        if not self.SPEC_KIND:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid SPEC_KIND"
            )
        if not self.MAIN_CONTAINER_ID:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid MAIN_CONTAINER_ID"
            )

    @staticmethod
    def get_by_name(values: List[Any]) -> Dict[str, Any]:
        return {c.name: c for c in values}

    @staticmethod
    def get_api_host(external_host: bool = False) -> str:
        if external_host:
            return get_api_host(default=settings.CLIENT_CONFIG.host)
        else:
            return clean_host(settings.CLIENT_CONFIG.host)

    @staticmethod
    def filter_connections_from_init(init: List[V1Init]) -> List[V1Init]:
        return [i for i in init if i.has_connection()]

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
    ) -> List[Union[k8s_schemas.V1EnvVar, docker_types.V1EnvVar]]:
        raise NotImplementedError

    def get_main_env_vars(
        self, external_host: bool = False, log_level: Optional[str] = None, **kwargs
    ) -> List[EnvVar]:
        if self.base_env_vars:
            return self._get_base_env_vars(
                namespace=self.namespace,
                resource_name=self.resource_name,
                use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
                log_level=log_level,
            )
        return self._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=external_host,
            log_level=log_level,
        )

    def get_polyaxon_sidecar_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> List[EnvVar]:
        if not self.base_env_vars:
            return self._get_service_env_vars(
                service_header=PolyaxonServices.SIDECAR,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env += [self._get_env_var(name=EV_KEYS_NO_API, value=True)]
        if log_level:
            env += [self._get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level)]
        proxy_env = self._get_proxy_env_vars(
            settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
        )
        if proxy_env:
            env += proxy_env
        return env

    def get_auth_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[EnvVar]]:
        if self.base_env_vars:
            return None
        return self._get_service_env_vars(
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
    ) -> Optional[List[EnvVar]]:
        if not self.base_env_vars:
            return self._get_service_env_vars(
                service_header=PolyaxonServices.INITIALIZER,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env.append(self._get_env_var(name=EV_KEYS_NO_API, value=True))
        if log_level:
            env.append(self._get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level))
        proxy_env = self._get_proxy_env_vars(
            settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
        )
        if proxy_env:
            env += proxy_env
        return env

    def filter_containers_from_init(
        self, init: List[V1Init]
    ) -> List[k8s_schemas.V1Container]:
        return [i.container for i in init if not i.has_connection()]

    @staticmethod
    def _get_env_var(name: str, value: Any) -> EnvVar:
        raise NotImplementedError

    @staticmethod
    def _get_proxy_env_vars(use_proxy_env_vars_use_in_ops: bool) -> List[EnvVar]:
        raise NotImplementedError

    @staticmethod
    def _get_base_env_vars(
        namespace: str,
        resource_name: str,
        use_proxy_env_vars_use_in_ops: bool,
        log_level: Optional[str],
    ) -> List[EnvVar]:
        raise NotImplementedError

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
    ) -> Container:
        raise NotImplementedError

    @staticmethod
    def _get_custom_init_container(
        connection: V1Connection,
        plugins: V1Plugins,
        container: Optional[k8s_schemas.V1Container],
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> Container:
        raise NotImplementedError

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
    ) -> Container:
        raise NotImplementedError

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
    ) -> Container:
        raise NotImplementedError

    @staticmethod
    def _get_git_init_container(
        polyaxon_init: V1PolyaxonInitContainer,
        connection: V1Connection,
        plugins: V1Plugins,
        container: Optional[k8s_schemas.V1Container] = None,
        env: List[k8s_schemas.V1EnvVar] = None,
        mount_path: Optional[str] = None,
        track: bool = False,
    ) -> Container:
        raise NotImplementedError

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
    ) -> Container:
        raise NotImplementedError

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
    ) -> Container:
        raise NotImplementedError

    @staticmethod
    def _get_auth_context_container(
        polyaxon_init: V1PolyaxonInitContainer,
        env: Optional[List[k8s_schemas.V1EnvVar]] = None,
    ) -> Container:
        raise NotImplementedError

    @staticmethod
    def _get_artifacts_path_container(
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        run_path: str,
        auto_resume: bool,
        env: Optional[List[k8s_schemas.V1EnvVar]] = None,
    ) -> Container:
        raise NotImplementedError

    def _handle_init_connections(
        self,
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        init_connections: List[V1Init],
        connection_by_names: Dict[str, V1Connection],
        plugins: V1Plugins,
        log_level: Optional[str] = None,
    ) -> List[Container]:
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
                        self._get_git_init_container(
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
                        self._get_git_init_container(
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
                        self._get_store_container(
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
                        self._get_custom_init_container(
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
                        self._get_store_container(
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
                        self._get_git_init_container(
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
                        self._get_dockerfile_init_container(
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
                        self._get_file_init_container(
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
                        self._get_tensorboard_init_container(
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
                self._get_auth_context_container(
                    polyaxon_init=polyaxon_init,
                    env=self.get_auth_service_env_vars(
                        external_host=plugins.external_host
                    ),
                )
            )

        # Add outputs
        if plugins and plugins.collect_artifacts:
            containers += to_list(
                self._get_artifacts_path_container(
                    polyaxon_init=polyaxon_init,
                    artifacts_store=artifacts_store,
                    run_path=self.run_path,
                    auto_resume=plugins.auto_resume,
                    env=self._get_proxy_env_vars(
                        settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
                    ),
                ),
                check_none=True,
            )

        containers += self._handle_init_connections(
            polyaxon_init=polyaxon_init,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
            plugins=plugins,
            log_level=log_level,
        )
        return containers + init_containers

    def get_main_container(
        self,
        main_container: k8s_schemas.V1Container,
        plugins: V1Plugins,
        artifacts_store: V1Connection,
        connections: List[str],
        init_connections: Optional[List[V1Init]],
        connection_by_names: Dict[str, V1Connection],
        log_level: str,
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        kv_env_vars: List[List] = None,
        ports: List[int] = None,
    ) -> Container:
        env = self.get_main_env_vars(
            external_host=plugins.external_host if plugins else False,
            log_level=log_level,
        )
        return self._get_main_container(
            container_id=self.MAIN_CONTAINER_ID,
            main_container=main_container,
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

    def get_resource(self, **kwargs) -> ResourceSpec:
        raise NotImplementedError
