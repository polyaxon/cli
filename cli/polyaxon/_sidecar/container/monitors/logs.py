import datetime

from typing import Optional

import aiofiles

from clipped.utils.paths import check_or_create_path, set_permissions
from kubernetes_asyncio.client.models import V1Pod

from polyaxon._contexts import paths as ctx_paths
from polyaxon._k8s.logging.async_monitor import query_k8s_pod_logs
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from traceml.logging import V1Logs
from traceml.events import get_logs_path


async def sync_logs(
    run_uuid: str,
    k8s_manager: AsyncK8sManager,
    pod: V1Pod,
    last_time: Optional[datetime.datetime],
    stream: bool = False,
) -> Optional[datetime.datetime]:
    logs, last_time = await query_k8s_pod_logs(
        k8s_manager=k8s_manager,
        pod=pod,
        last_time=last_time,
        stream=stream,
    )
    if not logs:
        return last_time

    path_from = get_logs_path(
        run_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_uuid),
        filename=pod.metadata.name,
    )
    check_or_create_path(path_from, is_dir=False)
    async with aiofiles.open(path_from, "a") as outfile:
        _logs = V1Logs.construct(logs=logs)
        await outfile.write(_logs.get_jsonl_events())
    set_permissions(path_from)
    return last_time
