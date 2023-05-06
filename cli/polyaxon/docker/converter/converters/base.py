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
from typing import Any, Dict, Iterable, List, Optional

from polyaxon import settings
from polyaxon.api import VERSION_V1
from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.docker import docker_types
from polyaxon.docker.converter.common.env_vars import (
    get_base_env_vars,
    get_env_var,
    get_proxy_env_vars,
    get_service_env_vars,
)
from polyaxon.docker.converter.common.volumes import get_pod_volumes
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.polyflow import V1Environment, V1Init, V1Plugins
from polyaxon.runner.converter import BaseConverter as _BaseConverter
from polyaxon.services.headers import PolyaxonServiceHeaders


class BaseConverter(_BaseConverter):
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
            use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
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

    def get_container_cmd(
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
    ) -> List[str]:
        if volumes:
            raise PolyaxonConverterError(
                "Volumes are not supported by the docker executor please use connections instead."
            )
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

        return CommandSpec(
            volumes=volumes,
            init_containers=init_containers,
            sidecar_containers=sidecar_containers,
            main_container=main_container,
            environment=environment,
            num_replicas=num_replicas,
        )
