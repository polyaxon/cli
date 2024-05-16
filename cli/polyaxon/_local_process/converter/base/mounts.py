from typing import List, Optional

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._contexts import paths as ctx_paths
from polyaxon._local_process import process_types
from polyaxon._runner.converter import BaseConverter


class MountsMixin(BaseConverter):
    @classmethod
    def _get_mount_from_store(
        cls,
        store: V1Connection,
    ):
        pass

    @classmethod
    def _get_mount_from_resource(
        cls,
        resource: V1ConnectionResource,
    ):
        pass

    @classmethod
    def _get_volume(
        cls,
        mount_path: str,
        host_path: Optional[str] = None,
        read_only: Optional[bool] = None,
    ):
        pass

    @classmethod
    def _get_docker_context_mount(cls):
        pass

    @classmethod
    def _get_auth_context_mount(
        cls,
        read_only: Optional[bool] = None,
        run_path: Optional[str] = None,
    ):
        pass

    @classmethod
    def _get_artifacts_context_mount(
        cls,
        read_only: bool = False,
        run_path: Optional[str] = None,
    ):
        pass

    @classmethod
    def _get_connections_context_mount(
        cls,
        name: str,
        mount_path: str,
        run_path: str,
    ):
        pass

    @classmethod
    def _get_shm_context_mount(cls):
        """
        Mount a tmpfs volume to /dev/shm.
        This will set /dev/shm size to half of the RAM of node.
        By default, /dev/shm is very small, only 64MB.
        Some experiments will fail due to lack of share memory,
        such as some experiments running on Pytorch.
        """
        pass

    @classmethod
    def _get_mounts(
        cls,
        use_auth_context: bool,
        use_docker_context: bool,
        use_shm_context: bool,
        use_artifacts_context: bool,
        run_path: Optional[str] = None,
    ) -> List:
        return []
