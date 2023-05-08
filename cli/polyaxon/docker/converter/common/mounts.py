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
from typing import List, Optional

from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.contexts import paths as ctx_paths
from polyaxon.docker import docker_types


def _get_volume(
    host_path: str, mount_path: str, read_only: bool
) -> docker_types.V1VolumeMount:
    volume = f"{host_path}:{mount_path}"
    if read_only:
        volume += ":ro"
    return "-v", volume


def _get_mount(mount_path: str, read_only: bool) -> docker_types.V1VolumeMount:
    mount = f"type=tmpfs,destination={mount_path}"
    if read_only:
        mount += ",ro"
    return "--mount", mount


def get_config_volume() -> docker_types.V1VolumeMount:
    return _get_volume(
        ctx_paths.CONTEXT_USER_POLYAXON_PATH, ctx_paths.CONTEXT_TMP_POLYAXON_PATH, True
    )


def get_mount_from_store(
    connection: V1Connection,
) -> Optional[docker_types.V1VolumeMount]:
    if not connection:
        return None
    if connection.is_volume_claim:
        return _get_volume(
            connection.schema_.volume_claim,
            connection.schema_.mount_path,
            connection.schema_.read_only,
        )

    if connection.is_host_path:
        return _get_volume(
            connection.schema_.host_path,
            connection.schema_.mount_path,
            connection.schema_.read_only,
        )


def get_mount_from_resource(
    resource: V1ConnectionResource,
) -> Optional[docker_types.V1VolumeMount]:
    if not resource:
        return None
    if resource.mount_path:
        return _get_volume(resource.host_path, resource.mount_path, True)


def get_volume(
    mount_path: str,
    host_path: Optional[str] = None,
    read_only: Optional[bool] = None,
) -> Optional[docker_types.V1VolumeMount]:
    if host_path:
        return _get_volume(host_path, mount_path, read_only)

    return _get_mount(mount_path, read_only)


def get_docker_context_mount() -> docker_types.V1VolumeMount:
    return _get_volume(
        mount_path=ctx_paths.CONTEXT_MOUNT_DOCKER,
        host_path=ctx_paths.CONTEXT_MOUNT_DOCKER,
        read_only=True,
    )


def get_configs_context_mount() -> docker_types.V1VolumeMount:
    return _get_mount(mount_path=ctx_paths.CONTEXT_MOUNT_CONFIGS, read_only=False)


def get_auth_context_mount(read_only: bool = False) -> docker_types.V1VolumeMount:
    return _get_mount(mount_path=ctx_paths.CONTEXT_MOUNT_CONFIGS, read_only=read_only)


def get_artifacts_context_mount(read_only: bool = False) -> docker_types.V1VolumeMount:
    return _get_volume(
        host_path=ctx_paths.CONTEXT_ARCHIVES_ROOT,
        mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
        read_only=read_only,
    )


def get_connections_context_mount(mount_path: str) -> docker_types.V1VolumeMount:
    return _get_mount(mount_path=mount_path, read_only=False)


def get_shm_context_mount() -> docker_types.V1VolumeMount:
    """
    Mount an tmpfs volume to /dev/shm.
    This will set /dev/shm size to half of the RAM of node.
    By default, /dev/shm is very small, only 64MB.
    Some experiments will fail due to lack of share memory,
    such as some experiments running on Pytorch.
    """
    return _get_mount(mount_path=ctx_paths.CONTEXT_MOUNT_SHM, read_only=False)


def get_mounts(
    use_auth_context: bool,
    use_docker_context: bool,
    use_shm_context: bool,
    use_artifacts_context: bool,
) -> List[docker_types.V1VolumeMount]:
    mounts = []
    if use_auth_context:
        mounts.append(get_auth_context_mount(read_only=True))
    if use_artifacts_context:
        mounts.append(get_artifacts_context_mount(read_only=False))
    if use_docker_context:
        mounts.append(get_docker_context_mount())
    if use_shm_context:
        mounts.append(get_shm_context_mount())

    return mounts
