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

from polyaxon import settings
from polyaxon.api import VERSION_V1
from polyaxon.auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.docker import docker_types
from polyaxon.docker.converter.common.env_vars import (
    get_base_env_vars,
    get_env_var,
    get_proxy_env_vars,
    get_service_env_vars,
)
from polyaxon.docker.converter.common.mounts import get_volume
from polyaxon.docker.converter.init.artifacts import get_artifacts_path_container
from polyaxon.docker.converter.init.auth import get_auth_context_container
from polyaxon.docker.converter.init.custom import get_custom_init_container
from polyaxon.docker.converter.init.dockerfile import get_dockerfile_init_container
from polyaxon.docker.converter.init.file import get_file_init_container
from polyaxon.docker.converter.init.git import get_git_init_container
from polyaxon.docker.converter.init.store import get_store_container
from polyaxon.docker.converter.init.tensorboard import get_tensorboard_init_container
from polyaxon.docker.converter.main.container import get_main_container
from polyaxon.k8s import k8s_schemas
from polyaxon.polyflow import V1Environment, V1Init, V1Plugins
from polyaxon.runner.converter import BaseConverter as _BaseConverter
from polyaxon.runner.kind import RunnerKind
from polyaxon.schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1TensorboardType,
)
from polyaxon.services.headers import PolyaxonServiceHeaders


class BaseConverter(_BaseConverter):
    RUNNER_KIND = RunnerKind.DOCKER

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
    ) -> List[docker_types.V1EnvVar]:
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
    ) -> List[docker_types.V1EnvVar]:
        return get_base_env_vars(
            namespace=namespace,
            resource_name=resource_name,
            use_proxy_env_vars_use_in_ops=use_proxy_env_vars_use_in_ops,
            log_level=log_level,
        )

    @staticmethod
    def _get_env_var(name: str, value: Any) -> docker_types.V1EnvVar:
        raise get_env_var(name=name, value=value)

    @staticmethod
    def _get_proxy_env_vars(
        use_proxy_env_vars_use_in_ops: bool,
    ) -> List[docker_types.V1EnvVar]:
        return get_proxy_env_vars(
            use_proxy_env_vars_use_in_ops=use_proxy_env_vars_use_in_ops
        )

    @staticmethod
    def _get_sidecar_container(
        container_id: str,
        polyaxon_sidecar: V1PolyaxonSidecarContainer,
        env: List[docker_types.V1EnvVar],
        artifacts_store: V1Connection,
        plugins: V1Plugins,
        run_path: Optional[str],
    ) -> Optional[docker_types.V1Container]:
        return None

    @staticmethod
    def _get_main_container(
        container_id: str,
        main_container: docker_types.V1Container,
        plugins: V1Plugins,
        artifacts_store: Optional[V1Connection],
        init: Optional[List[V1Init]],
        connections: Optional[List[str]],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        run_path: Optional[str],
        kv_env_vars: List[List] = None,
        env: List[docker_types.V1EnvVar] = None,
        ports: List[int] = None,
    ) -> docker_types.V1Container:
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
        container: Optional[docker_types.V1Container],
        env: List[docker_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> docker_types.V1Container:
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
        container: Optional[docker_types.V1Container] = None,
        env: List[docker_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> docker_types.V1Container:
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
        container: Optional[docker_types.V1Container] = None,
        env: List[docker_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> docker_types.V1Container:
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
        container: Optional[docker_types.V1Container] = None,
        env: List[docker_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
        track: bool = False,
    ) -> docker_types.V1Container:
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
        container: Optional[docker_types.V1Container] = None,
        env: List[docker_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
        is_default_artifacts_store: bool = False,
    ) -> docker_types.V1Container:
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
        container: Optional[docker_types.V1Container] = None,
        env: List[docker_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> docker_types.V1Container:
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
        env: Optional[List[docker_types.V1EnvVar]] = None,
    ) -> docker_types.V1Container:
        return get_auth_context_container(polyaxon_init=polyaxon_init, env=env)

    @staticmethod
    def _get_artifacts_path_container(
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        run_path: str,
        auto_resume: bool,
        env: Optional[List[docker_types.V1EnvVar]] = None,
    ) -> docker_types.V1Container:
        return get_artifacts_path_container(
            polyaxon_init=polyaxon_init,
            artifacts_store=artifacts_store,
            run_path=run_path,
            auto_resume=auto_resume,
            env=env,
        )

    @staticmethod
    def _k8s_to_docker_env_var(
        env_var: List[k8s_schemas.V1EnvVar],
    ) -> List[docker_types.V1EnvVar]:
        if not env_var:
            return []

        docker_env_var = []
        for item in env_var:
            docker_env_var.append(get_env_var(name=item.name, value=item.value))

        return docker_env_var

    @staticmethod
    def _k8s_to_docker_volume_mounts(
        volume_mounts: List[k8s_schemas.V1VolumeMount],
        volumes: List[k8s_schemas.V1Volume],
    ) -> List[docker_types.V1VolumeMount]:
        if not volume_mounts or not volumes:
            return []

        docker_volume_mounts = []
        volumes_by_name = {item.name: item for item in volumes}
        for item in volume_mounts:
            volume = volumes_by_name.get(item.name)  # type: k8s_schemas.V1Volume
            if not volume:
                continue
            if volume.host_path:
                host_path = volume.host_path.path
            elif volume.persistent_volume_claim:
                host_path = volume.persistent_volume_claim.claim_name
            else:
                host_path = None
            docker_volume_mounts.append(
                get_volume(
                    mount_path=item.mount_path,
                    host_path=host_path,
                    read_only=item.read_only,
                )
            )

        return docker_volume_mounts

    @staticmethod
    def _k8s_to_docker_resources(
        resources: k8s_schemas.V1ResourceRequirements,
    ) -> Optional[docker_types.V1ResourceRequirements]:
        if not resources:
            return None

        cpus = None
        memory = None
        gpus = None
        if resources.limits:
            cpus = resources.limits.get("cpu")
            memory = resources.limits.get("memory")
            gpus = resources.limits.get("nvidia.com/gpu")
        if resources.requests:
            cpus = cpus or resources.requests.get("cpu")
            memory = memory or resources.requests.get("memory")
            gpus = gpus or resources.requests.get("nvidia.com/gpu")
        docker_resources = {}
        if cpus:
            docker_resources["cpu"] = cpus
        if memory:
            docker_resources["memory"] = memory
        if gpus:
            docker_resources[gpus] = gpus
        return docker_types.V1ResourceRequirements.from_dict(docker_resources)

    @classmethod
    def _ensure_container(
        cls,
        container: Union[k8s_schemas.V1Container, docker_types.V1Container],
        volumes: List[k8s_schemas.V1Volume],
    ) -> docker_types.V1Container:
        if not isinstance(container, k8s_schemas.V1Container):
            return container
        return docker_types.V1Container(
            name=container.name,
            image=container.image,
            command=container.command,
            args=container.args,
            env=cls._k8s_to_docker_env_var(container.env),
            volumes=cls._k8s_to_docker_volume_mounts(container.volume_mounts, volumes),
            resources=cls._k8s_to_docker_resources(container.resources),
            working_dir=container.working_dir,
        )

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
    ) -> List[docker_types.V1Container]:
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

        init_containers = self.get_init_containers(
            polyaxon_init=self.polyaxon_init,
            plugins=plugins,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            init_containers=self.filter_containers_from_init(init=init),
            connection_by_names=connection_by_names,
            log_level=plugins.log_level,
            volumes=volumes,
        )

        sidecar_containers = self.get_sidecar_containers(
            polyaxon_sidecar=self.polyaxon_sidecar,
            plugins=plugins,
            artifacts_store=artifacts_store,
            sidecar_containers=sidecars,
            log_level=plugins.log_level,
            volumes=volumes,
        )

        main_container = self.get_main_container(
            main_container=self._ensure_container(container, volumes=volumes),
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

        return init_containers + sidecar_containers + [main_container]
