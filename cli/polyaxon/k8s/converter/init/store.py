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

import os

from typing import List, Optional, Tuple, Union

from clipped.utils.enums import get_enum_value
from clipped.utils.lists import to_list

from polyaxon.auxiliaries import V1PolyaxonInitContainer
from polyaxon.connections import V1Connection
from polyaxon.containers.names import (
    INIT_ARTIFACTS_CONTAINER_PREFIX,
    generate_container_name,
)
from polyaxon.contexts import paths as ctx_paths
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.containers import patch_container
from polyaxon.k8s.converter.common.env_vars import (
    get_connection_env_var,
    get_connections_catalog_env_var,
    get_env_from_config_map,
    get_env_from_secret,
    get_items_from_config_map,
    get_items_from_secret,
)
from polyaxon.k8s.converter.common.mounts import (
    get_connections_context_mount,
    get_mount_from_resource,
    get_mount_from_store,
)
from polyaxon.k8s.converter.common.volumes import get_volume_name
from polyaxon.runner.converter.common import constants
from polyaxon.runner.converter.init.store import get_volume_args
from polyaxon.schemas.types import V1ArtifactsType


def get_base_store_container(
    container: Optional[k8s_schemas.V1Container],
    container_name: str,
    polyaxon_init: V1PolyaxonInitContainer,
    store: V1Connection,
    env: List[k8s_schemas.V1EnvVar],
    env_from: List[k8s_schemas.V1EnvFromSource],
    volume_mounts: List[k8s_schemas.V1VolumeMount],
    args: List[str],
    command: Optional[List[str]] = None,
) -> Optional[k8s_schemas.V1Container]:
    env = env or []
    env_from = env_from or []
    volume_mounts = volume_mounts or []

    # Artifact store needs to allow init the contexts as well, so the store is not required
    if not store:
        raise PolyaxonConverterError("Init store container requires a store")

    if store.is_bucket:
        secret = store.secret
        volume_mounts = volume_mounts + to_list(
            get_mount_from_resource(resource=secret), check_none=True
        )
        env = env + to_list(get_items_from_secret(secret=secret), check_none=True)
        env_from = env_from + to_list(
            get_env_from_secret(secret=secret), check_none=True
        )
        config_map = store.config_map
        volume_mounts = volume_mounts + to_list(
            get_mount_from_resource(resource=config_map), check_none=True
        )
        env = env + to_list(
            get_items_from_config_map(config_map=config_map), check_none=True
        )
        env_from = env_from + to_list(
            get_env_from_config_map(config_map=config_map), check_none=True
        )
    else:
        volume_mounts = volume_mounts + to_list(
            get_mount_from_store(store=store), check_none=True
        )
    # Add connections catalog env vars information
    env += to_list(
        get_connections_catalog_env_var(connections=[store]),
        check_none=True,
    )
    env += to_list(get_connection_env_var(connection=store), check_none=True)

    return patch_container(
        container=container,
        name=container_name,
        image=polyaxon_init.get_image(),
        image_pull_policy=polyaxon_init.image_pull_policy,
        command=command or ["/bin/sh", "-c"],
        args=args,
        env=env,
        env_from=env_from,
        resources=polyaxon_init.get_resources(),
        volume_mounts=volume_mounts,
    )


def get_store_container(
    polyaxon_init: V1PolyaxonInitContainer,
    connection: V1Connection,
    artifacts: V1ArtifactsType,
    paths: Union[List[str], List[Tuple[str, str]]],
    container: Optional[k8s_schemas.V1Container] = None,
    env: List[k8s_schemas.V1EnvVar] = None,
    mount_path: Optional[str] = None,
    is_default_artifacts_store: bool = False,
) -> Optional[k8s_schemas.V1Container]:
    container_name = generate_container_name(
        INIT_ARTIFACTS_CONTAINER_PREFIX, connection.name
    )
    if not container:
        container = k8s_schemas.V1Container(name=container_name)

    volume_name = (
        get_volume_name(mount_path) if mount_path else constants.VOLUME_MOUNT_ARTIFACTS
    )
    volume_mount_path = mount_path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS
    volume_mounts = [
        get_connections_context_mount(name=volume_name, mount_path=volume_mount_path)
    ]
    mount_path = mount_path or (
        ctx_paths.CONTEXT_MOUNT_ARTIFACTS
        if is_default_artifacts_store
        else ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(connection.name)
    )

    return get_base_store_container(
        container=container,
        container_name=container_name,
        polyaxon_init=polyaxon_init,
        store=connection,
        env=env,
        env_from=[],
        volume_mounts=volume_mounts,
        args=[
            get_volume_args(
                store=connection,
                mount_path=mount_path,
                artifacts=artifacts,
                paths=paths,
            )
        ],
    )
