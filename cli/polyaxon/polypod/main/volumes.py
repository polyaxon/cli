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

from typing import Iterable, List, Optional

from clipped.utils.lists import to_list

from polyaxon.connections import V1Connection, V1K8sResource
from polyaxon.contexts import paths as ctx_paths
from polyaxon.k8s import constants, k8s_schemas
from polyaxon.k8s.mounts import (
    get_artifacts_context_mount,
    get_connections_context_mount,
    get_mount_from_resource,
    get_mount_from_store,
)
from polyaxon.k8s.volumes import get_volume_name
from polyaxon.polyflow import V1Init, V1Plugins


def get_volume_mounts(
    plugins: V1Plugins,
    init: Optional[List[V1Init]],
    connections: Iterable[V1Connection],
    secrets: Iterable[V1K8sResource],
    config_maps: Iterable[V1K8sResource] = None,
) -> List[k8s_schemas.V1VolumeMount]:
    init = init or []
    connections = connections or []
    secrets = secrets or []
    config_maps = config_maps or []

    volume_mounts = []
    volume_names = set()
    if plugins and plugins.collect_artifacts:
        volume_mounts += to_list(
            get_artifacts_context_mount(read_only=False), check_none=True
        )
        volume_names.add(constants.VOLUME_MOUNT_ARTIFACTS)
    for init_connection in init:
        volume_name = (
            get_volume_name(init_connection.path)
            if init_connection.path
            else constants.VOLUME_MOUNT_ARTIFACTS
        )
        mount_path = init_connection.path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS
        if volume_name in volume_names:
            continue
        volume_names.add(volume_name)
        volume_mounts += to_list(
            get_connections_context_mount(name=volume_name, mount_path=mount_path),
            check_none=True,
        )
    for store in connections:
        volume_mounts += to_list(get_mount_from_store(store=store), check_none=True)

    for secret in secrets:
        volume_mounts += to_list(
            get_mount_from_resource(resource=secret), check_none=True
        )

    for config_map in config_maps:
        volume_mounts += to_list(
            get_mount_from_resource(resource=config_map), check_none=True
        )

    return volume_mounts
