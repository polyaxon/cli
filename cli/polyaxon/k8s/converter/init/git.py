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

from typing import List, Optional

from clipped.utils.json import orjson_dumps
from clipped.utils.lists import to_list

from polyaxon.auxiliaries import V1PolyaxonInitContainer
from polyaxon.connections import V1Connection, V1ConnectionKind
from polyaxon.containers.names import INIT_GIT_CONTAINER_PREFIX, generate_container_name
from polyaxon.contexts import paths as ctx_paths
from polyaxon.env_vars.keys import EV_KEYS_SSH_PATH
from polyaxon.exceptions import PolypodException
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common import constants
from polyaxon.k8s.converter.common.containers import patch_container
from polyaxon.k8s.converter.common.env_vars import (
    get_connection_env_var,
    get_connections_catalog_env_var,
    get_env_from_config_map,
    get_env_from_secret,
    get_env_var,
    get_items_from_config_map,
    get_items_from_secret,
)
from polyaxon.k8s.converter.common.mounts import (
    get_auth_context_mount,
    get_connections_context_mount,
    get_mount_from_resource,
)
from polyaxon.k8s.converter.common.volumes import get_volume_name
from polyaxon.polyflow import V1Plugins


def get_repo_context_args(
    name: str,
    url: str,
    revision: str,
    mount_path: str,
    connection: Optional[str] = None,
    flags: Optional[List[str]] = None,
) -> List[str]:
    if not name:
        raise PolypodException("A repo name is required to create a repo context.")
    if not url:
        raise PolypodException("A repo url is required to create a repo context.")

    args = [
        "--repo-path={}".format(os.path.join(mount_path, name)),
        "--url={}".format(url),
    ]

    if revision:
        args.append("--revision={}".format(revision))

    if connection:
        args.append("--connection={}".format(connection))

    flags = to_list(flags, check_none=True)
    if flags:
        args.append("--flags={}".format(orjson_dumps(flags)))
    return args


def get_git_init_container(
    polyaxon_init: V1PolyaxonInitContainer,
    connection: V1Connection,
    plugins: V1Plugins,
    container: Optional[k8s_schemas.V1Container] = None,
    env: List[k8s_schemas.V1EnvVar] = None,
    mount_path: Optional[str] = None,
    track: bool = False,
) -> k8s_schemas.V1Container:
    if not connection:
        raise PolypodException("A connection is required to create a repo context.")
    container_name = generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name)
    if not container:
        container = k8s_schemas.V1Container(name=container_name)

    volume_name = (
        get_volume_name(mount_path) if mount_path else constants.VOLUME_MOUNT_ARTIFACTS
    )
    mount_path = mount_path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS
    volume_mounts = [
        get_connections_context_mount(name=volume_name, mount_path=mount_path)
    ]

    if plugins and plugins.auth:
        volume_mounts.append(get_auth_context_mount(read_only=True))

    env = to_list(env, check_none=True)
    env_from = []
    secret = connection.secret
    if secret:
        volume_mounts += to_list(
            get_mount_from_resource(resource=secret), check_none=True
        )
        env += to_list(get_items_from_secret(secret=secret), check_none=True)
        env_from = to_list(get_env_from_secret(secret=secret), check_none=True)

    # Add connections catalog env vars information
    env += to_list(
        get_connections_catalog_env_var(connections=[connection]),
        check_none=True,
    )
    env += to_list(get_connection_env_var(connection=connection), check_none=True)
    # Add special handling to auto-inject ssh mount path
    if connection.kind == V1ConnectionKind.SSH and secret.mount_path:
        env += [get_env_var(EV_KEYS_SSH_PATH, secret.mount_path)]
    config_map = connection.config_map
    if config_map:
        volume_mounts += to_list(
            get_mount_from_resource(resource=config_map), check_none=True
        )
        env += to_list(
            get_items_from_config_map(config_map=config_map), check_none=True
        )
        env_from = to_list(
            get_env_from_config_map(config_map=config_map), check_none=True
        )
    args = get_repo_context_args(
        name=connection.name,
        # Handle the case of custom connection
        url=getattr(connection.schema_, "url", None),
        revision=getattr(connection.schema_, "revision", None),
        flags=getattr(connection.schema_, "flags", None),
        mount_path=mount_path,
        connection=connection.name if track else None,
    )
    return patch_container(
        container=container,
        name=container_name,
        image=polyaxon_init.get_image(),
        image_pull_policy=polyaxon_init.image_pull_policy,
        command=["polyaxon", "initializer", "git"],
        args=args,
        env=env,
        env_from=env_from,
        volume_mounts=volume_mounts,
        resources=polyaxon_init.get_resources(),
    )