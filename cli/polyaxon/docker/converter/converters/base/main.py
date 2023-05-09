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

from typing import Dict, Iterable, List, Optional

from clipped.utils.lists import to_list

from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.docker import docker_types
from polyaxon.docker.converter.common.containers import patch_container
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.polyflow import V1Init, V1Plugins
from polyaxon.runner.converter import BaseConverter as _BaseConverter


class MainConverter(_BaseConverter):
    def _get_main_container(
        self,
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
        ports: List[int] = None,
    ) -> docker_types.V1Container:
        connections = connections or []
        connection_by_names = connection_by_names or {}
        secrets = secrets or []
        config_maps = config_maps or []

        if artifacts_store and not run_path:
            raise PolyaxonConverterError("Run path is required for main container.")

        if artifacts_store and (
            not plugins.collect_artifacts or plugins.mount_artifacts_store
        ):
            if artifacts_store.name not in connection_by_names:
                connection_by_names[artifacts_store.name] = artifacts_store
            if artifacts_store.name not in connections:
                connections.append(artifacts_store.name)

        requested_connections = [connection_by_names[c] for c in connections]
        requested_config_maps = V1Connection.get_requested_resources(
            resources=config_maps,
            connections=requested_connections,
            resource_key="config_map",
        )
        requested_secrets = V1Connection.get_requested_resources(
            resources=secrets, connections=requested_connections, resource_key="secret"
        )

        # Mounts
        volume_mounts = (
            self._get_mounts(
                use_auth_context=plugins.auth,
                use_artifacts_context=False,  # Main container has a check and handling for this
                use_docker_context=plugins.docker,
                use_shm_context=plugins.shm,
            )
            if plugins
            else []
        )
        volume_mounts = volume_mounts + self._get_main_volume_mounts(
            plugins=plugins,
            init=init,
            connections=requested_connections,
            secrets=requested_secrets,
            config_maps=requested_config_maps,
        )

        # Env vars
        env = self._get_main_env_vars(
            plugins=plugins,
            kv_env_vars=kv_env_vars,
            artifacts_store_name=artifacts_store.name if artifacts_store else None,
            connections=requested_connections,
            secrets=requested_secrets,
            config_maps=requested_config_maps,
        )

        # Env from
        resources = to_list(requested_secrets, check_none=True) + to_list(
            requested_config_maps, check_none=True
        )
        env += self._get_env_from_json_resources(resources=resources)

        ports = to_list(ports, check_none=True)

        return patch_container(
            container=main_container,
            name=container_id,
            env=env,
            volume_mounts=volume_mounts,
            ports=ports or None,
        )
