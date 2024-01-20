import aiofiles

from clipped.utils.json import orjson_dumps
from clipped.utils.paths import check_or_create_path

from polyaxon._contexts import paths as ctx_paths
from polyaxon._flow import V1RunKind
from polyaxon._k8s.logging.async_monitor import get_op_spec
from polyaxon._k8s.manager.async_manager import AsyncK8sManager


async def sync_spec(
    run_uuid: str,
    k8s_manager: AsyncK8sManager,
    run_kind: V1RunKind,
):
    op_spec, _, _ = await get_op_spec(
        k8s_manager=k8s_manager, run_uuid=run_uuid, run_kind=run_kind
    )
    path_from = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_uuid)
    path_from = "{}/outputs/spec.json".format(path_from)
    check_or_create_path(path_from, is_dir=False)
    async with aiofiles.open(path_from, "w") as filepath:
        await filepath.write(orjson_dumps(op_spec))
