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
from polyaxon.runner.converter import BaseConverter


class MountsMixin(BaseConverter):
    @staticmethod
    def _get_docker_volume(
        host_path: str, mount_path: str, read_only: bool
    ) -> docker_types.V1VolumeMount:
        volume = f"{host_path}:{mount_path}"
        if read_only:
            volume += ":ro"
        return "-v", volume

    @staticmethod
    def _get_docker_mount(
        mount_path: str, read_only: bool
    ) -> docker_types.V1VolumeMount:
        mount = f"type=tmpfs,destination={mount_path}"
        if read_only:
            mount += ",ro"
        return "--mount", mount

    @classmethod
    def _get_config_volume(cls) -> docker_types.V1VolumeMount:
        return cls._get_docker_volume(
            ctx_paths.CONTEXT_USER_POLYAXON_PATH,
            ctx_paths.CONTEXT_TMP_POLYAXON_PATH,
            True,
        )

    @classmethod
    def _get_mount_from_store(
        cls,
        store: V1Connection,
    ) -> Optional[docker_types.V1VolumeMount]:
        if not store:
            return None
        if store.is_volume_claim:
            return cls._get_docker_volume(
                store.schema_.volume_claim,
                store.schema_.mount_path,
                store.schema_.read_only,
            )

        if store.is_host_path:
            return cls._get_docker_volume(
                store.schema_.host_path,
                store.schema_.mount_path,
                store.schema_.read_only,
            )

    @classmethod
    def _get_mount_from_resource(
        cls,
        resource: V1ConnectionResource,
    ) -> Optional[docker_types.V1VolumeMount]:
        if not resource:
            return None
        if resource.mount_path:
            return cls._get_docker_volume(resource.host_path, resource.mount_path, True)

    @classmethod
    def _get_volume(
        cls,
        mount_path: str,
        host_path: Optional[str] = None,
        read_only: Optional[bool] = None,
    ) -> Optional[docker_types.V1VolumeMount]:
        if host_path:
            return cls._get_docker_volume(host_path, mount_path, read_only)

        return cls._get_docker_mount(mount_path, read_only)

    @classmethod
    def _get_docker_context_mount(cls) -> docker_types.V1VolumeMount:
        return cls._get_docker_volume(
            mount_path=ctx_paths.CONTEXT_MOUNT_DOCKER,
            host_path=ctx_paths.CONTEXT_MOUNT_DOCKER,
            read_only=True,
        )

    @classmethod
    def _get_configs_context_mount(cls) -> docker_types.V1VolumeMount:
        return cls._get_volume(
            mount_path=ctx_paths.CONTEXT_MOUNT_CONFIGS, read_only=False
        )

    @classmethod
    def _get_auth_context_mount(
        cls, read_only: bool = False
    ) -> docker_types.V1VolumeMount:
        return cls._get_volume(
            mount_path=ctx_paths.CONTEXT_MOUNT_CONFIGS, read_only=read_only
        )

    @classmethod
    def _get_artifacts_context_mount(
        cls, read_only: bool = False
    ) -> docker_types.V1VolumeMount:
        return cls._get_docker_volume(
            host_path=ctx_paths.CONTEXT_ARCHIVES_ROOT,
            mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            read_only=read_only,
        )

    @classmethod
    def _get_connections_context_mount(
        cls, name: str, mount_path: str
    ) -> docker_types.V1VolumeMount:
        return cls._get_volume(mount_path=mount_path, read_only=False)

    @classmethod
    def _get_shm_context_mount(cls) -> docker_types.V1VolumeMount:
        """
        Mount an tmpfs volume to /dev/shm.
        This will set /dev/shm size to half of the RAM of node.
        By default, /dev/shm is very small, only 64MB.
        Some experiments will fail due to lack of share memory,
        such as some experiments running on Pytorch.
        """
        return cls._get_volume(mount_path=ctx_paths.CONTEXT_MOUNT_SHM, read_only=False)

    @classmethod
    def _get_mounts(
        cls,
        use_auth_context: bool,
        use_docker_context: bool,
        use_shm_context: bool,
        use_artifacts_context: bool,
    ) -> List[docker_types.V1VolumeMount]:
        mounts = []
        if use_auth_context:
            mounts.append(cls._get_auth_context_mount(read_only=True))
        if use_artifacts_context:
            mounts.append(cls._get_artifacts_context_mount(read_only=False))
        if use_docker_context:
            mounts.append(cls._get_docker_context_mount())
        if use_shm_context:
            mounts.append(cls._get_shm_context_mount())

        return mounts
