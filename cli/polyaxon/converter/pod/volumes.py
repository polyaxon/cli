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

from polyaxon.connections import V1Connection, V1K8sResource
from polyaxon.converter.main.k8s_resources import (
    get_requested_config_maps,
    get_requested_secrets,
)
from polyaxon.k8s import constants, k8s_schemas
from polyaxon.k8s.volumes import (
    get_artifacts_context_volume,
    get_configs_context_volume,
    get_connections_context_volume,
    get_docker_context_volume,
    get_shm_context_volume,
    get_volume_from_config_map,
    get_volume_from_connection,
    get_volume_from_secret,
    get_volume_name,
)
from polyaxon.polyflow import V1Init, V1Plugins


def get_pod_volumes(
    plugins: Optional[V1Plugins],
    artifacts_store: Optional[V1Connection],
    init_connections: Optional[List[V1Init]],
    connections: List[str],
    connection_by_names: Optional[Dict[str, V1Connection]],
    secrets: Optional[Iterable[V1K8sResource]],
    config_maps: Optional[Iterable[V1K8sResource]],
    volumes: List[k8s_schemas.V1Volume] = None,
) -> List[k8s_schemas.V1Volume]:
    """Resolve all volumes that need to be mounted"""
    connections = to_list(connections, check_none=True)
    init_connections = to_list(init_connections, check_none=True)
    secrets = to_list(secrets, check_none=True)
    config_maps = to_list(config_maps, check_none=True)
    volumes = to_list(volumes, check_none=True)[:]
    connection_by_names = connection_by_names or {}

    requested_connection_names = connections[:]
    for init_connection in init_connections:
        if (
            init_connection.connection
            and init_connection.connection not in requested_connection_names
        ):
            requested_connection_names.append(init_connection.connection)
    if artifacts_store and artifacts_store.name not in requested_connection_names:
        requested_connection_names.append(artifacts_store.name)

    requested_connections = [connection_by_names[c] for c in requested_connection_names]

    requested_config_maps = get_requested_config_maps(
        config_maps=config_maps, connections=requested_connections
    )
    requested_secrets = get_requested_secrets(
        secrets=secrets, connections=requested_connections
    )

    def add_volume_from_connection(connection: V1Connection):
        volume = get_volume_from_connection(connection=connection)
        if volume:
            volumes.append(volume)

    def add_volume_from_resource(resource: V1K8sResource, is_secret: bool):
        if is_secret:
            volume = get_volume_from_secret(secret=resource)
        else:
            volume = get_volume_from_config_map(config_map=resource)
        if volume:
            volumes.append(volume)

    volume_names = set()
    connection_ids = set()
    # Handle context volumes from init section
    for init_connection in init_connections:
        volume_name = (
            get_volume_name(init_connection.path)
            if init_connection.path
            else constants.VOLUME_MOUNT_ARTIFACTS
        )
        if volume_name in volume_names:
            continue
        volume_names.add(volume_name)
        volumes.append(get_connections_context_volume(name=volume_name))

    # Add volumes from artifact stores
    for c_name in connection_by_names:
        connection = connection_by_names[c_name]
        if connection.name not in connection_ids:
            connection_ids.add(connection.name)
            add_volume_from_connection(connection=connection)
    # Add volumes from k8s config mount resources
    for secret in requested_secrets:
        add_volume_from_resource(resource=secret, is_secret=True)
    for config_map in requested_config_maps:
        add_volume_from_resource(resource=config_map, is_secret=False)

    # Add logs/outputs stores
    if plugins and (plugins.collect_artifacts or plugins.collect_logs):
        if constants.VOLUME_MOUNT_ARTIFACTS not in volume_names:
            volumes.append(get_artifacts_context_volume())
            volume_names.add(constants.VOLUME_MOUNT_ARTIFACTS)
        if artifacts_store and artifacts_store.name not in connection_ids:
            connection_ids.add(artifacts_store.name)
            add_volume_from_connection(connection=artifacts_store)

    # Add utils contexts
    if plugins and plugins.shm:
        volumes.append(get_shm_context_volume())
    if plugins and plugins.auth:
        volumes.append(get_configs_context_volume())
    if plugins and plugins.docker:
        volumes.append(get_docker_context_volume())
    return volumes
