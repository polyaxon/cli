import datetime

from typing import Optional

import aiofiles

from clipped.utils.paths import check_or_create_path, delete_path
from kubernetes_asyncio.client.models import V1Pod

from polyaxon._contexts import paths as ctx_paths
from polyaxon._k8s.logging.async_monitor import query_k8s_pod_logs
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from traceml.logging import V1Logs


async def sync_logs(
    run_uuid: str,
    k8s_manager: AsyncK8sManager,
    pod: V1Pod,
    last_time: Optional[datetime.datetime],
    stream: bool = False,
    is_running: bool = True,
):
    path_from = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_uuid)
    path_from = "{}/.tmpplxlogs".format(path_from)

    if not is_running:
        delete_path(path_from)
        return

    logs, _ = await query_k8s_pod_logs(
        k8s_manager=k8s_manager,
        pod=pod,
        last_time=last_time,
        stream=stream,
    )
    if not logs:
        return

    path_from = "{}/{}".format(path_from, pod.metadata.name)
    check_or_create_path(path_from, is_dir=False)
    async with aiofiles.open(path_from, "w") as filepath:
        _logs = V1Logs.construct(logs=logs)
        await filepath.write(_logs.to_json())
