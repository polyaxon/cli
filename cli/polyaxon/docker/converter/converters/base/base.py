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
from typing import Dict, Iterable, List, Optional, Union

from polyaxon import settings
from polyaxon.auxiliaries import V1PolyaxonSidecarContainer
from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.docker import docker_types
from polyaxon.k8s import k8s_schemas
from polyaxon.polyflow import V1Environment, V1Init, V1Plugins
from polyaxon.runner.converter import BaseConverter as _BaseConverter
from polyaxon.runner.kind import RunnerKind


class BaseConverter(_BaseConverter):
    RUNNER_KIND = RunnerKind.DOCKER

    @classmethod
    def _get_sidecar_container(
        cls,
        container_id: str,
        polyaxon_sidecar: V1PolyaxonSidecarContainer,
        env: List[docker_types.V1EnvVar],
        artifacts_store: V1Connection,
        plugins: V1Plugins,
        run_path: Optional[str],
    ) -> Optional[docker_types.V1Container]:
        return None

    @classmethod
    def _k8s_to_docker_env_var(
        cls,
        env_var: List[k8s_schemas.V1EnvVar],
    ) -> List[docker_types.V1EnvVar]:
        if not env_var:
            return []

        docker_env_var = []
        for item in env_var:
            docker_env_var.append(cls._get_env_var(name=item.name, value=item.value))

        return docker_env_var

    @classmethod
    def _k8s_to_docker_volume_mounts(
        cls,
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
                cls._get_volume(
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
            secrets=secrets,
            config_maps=config_maps,
            ports=ports,
            kv_env_vars=kv_env_vars,
        )

        return init_containers + sidecar_containers + [main_container]
