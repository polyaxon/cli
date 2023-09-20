from typing import List, Optional

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._contexts import paths as ctx_paths
from polyaxon._k8s import k8s_schemas
from polyaxon._runner.converter import BaseConverter
from polyaxon._runner.converter.common import constants


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
    def _get_auth_context_mount(
        read_only: Optional[bool] = None,
        run_path: Optional[str] = None,
    ) -> k8s_schemas.V1VolumeMount:
        return k8s_schemas.V1VolumeMount(
            name=constants.VOLUME_MOUNT_CONFIGS,
            mount_path=ctx_paths.CONTEXT_MOUNT_CONFIGS,
            read_only=read_only,
        )

    @staticmethod
    def _get_artifacts_context_mount(
        read_only: Optional[bool] = None,
        run_path: Optional[str] = None,
    ) -> k8s_schemas.V1VolumeMount:
        return k8s_schemas.V1VolumeMount(
            name=constants.VOLUME_MOUNT_ARTIFACTS,
            mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            read_only=read_only,
        )

    @staticmethod
    def _get_connections_context_mount(
        name: str, mount_path: str, run_path: str
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
        run_path: Optional[str] = None,
    ) -> List[k8s_schemas.V1VolumeMount]:
        mounts = []
        if use_auth_context:
            mounts.append(
                cls._get_auth_context_mount(read_only=True, run_path=run_path)
            )
        if use_artifacts_context:
            mounts.append(
                cls._get_artifacts_context_mount(read_only=False, run_path=run_path)
            )
        if use_docker_context:
            mounts.append(cls._get_docker_context_mount())
        if use_shm_context:
            mounts.append(cls._get_shm_context_mount())

        return mounts
