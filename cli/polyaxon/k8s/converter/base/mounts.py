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
from polyaxon.k8s import k8s_schemas
from polyaxon.runner.converter import BaseConverter
from polyaxon.runner.converter.common import constants


class MountsMixin(BaseConverter):
    @classmethod
    def _get_mount_from_store(
        cls, store: V1Connection
    ) -> Optional[k8s_schemas.V1VolumeMount]:
        if not store or not store.is_mount:
            return None

        return k8s_schemas.V1VolumeMount(
            name=store.name,
            mount_path=store.schema_.mount_path,
            read_only=store.schema_.read_only,
        )

    @staticmethod
    def _get_mount_from_resource(
        resource: V1ConnectionResource,
    ) -> Optional[k8s_schemas.V1VolumeMount]:
        if not resource or not resource.mount_path:
            return None

        return k8s_schemas.V1VolumeMount(
            name=resource.name, mount_path=resource.mount_path, read_only=True
        )

    @classmethod
    def _get_docker_context_mount(cls) -> k8s_schemas.V1VolumeMount:
        return k8s_schemas.V1VolumeMount(
            name=constants.VOLUME_MOUNT_DOCKER,
            mount_path=ctx_paths.CONTEXT_MOUNT_DOCKER,
        )

    @staticmethod
    def _get_auth_context_mount(read_only=None) -> k8s_schemas.V1VolumeMount:
        return k8s_schemas.V1VolumeMount(
            name=constants.VOLUME_MOUNT_CONFIGS,
            mount_path=ctx_paths.CONTEXT_MOUNT_CONFIGS,
            read_only=read_only,
        )

    @staticmethod
    def _get_artifacts_context_mount(
        read_only: Optional[bool] = None,
    ) -> k8s_schemas.V1VolumeMount:
        return k8s_schemas.V1VolumeMount(
            name=constants.VOLUME_MOUNT_ARTIFACTS,
            mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            read_only=read_only,
        )

    @staticmethod
    def _get_connections_context_mount(
        name: str, mount_path: str
    ) -> k8s_schemas.V1VolumeMount:
        return k8s_schemas.V1VolumeMount(name=name, mount_path=mount_path)

    @staticmethod
    def _get_shm_context_mount() -> k8s_schemas.V1VolumeMount:
        """
        Mount an tmpfs volume to /dev/shm.
        This will set /dev/shm size to half of the RAM of node.
        By default, /dev/shm is very small, only 64MB.
        Some experiments will fail due to lack of share memory,
        such as some experiments running on Pytorch.
        """
        return k8s_schemas.V1VolumeMount(
            name=constants.VOLUME_MOUNT_SHM, mount_path=ctx_paths.CONTEXT_MOUNT_SHM
        )

    @classmethod
    def _get_mounts(
        cls,
        use_auth_context: bool,
        use_docker_context: bool,
        use_shm_context: bool,
        use_artifacts_context: bool,
    ) -> List[k8s_schemas.V1VolumeMount]:
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