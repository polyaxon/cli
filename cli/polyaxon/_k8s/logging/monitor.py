from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from clipped.utils.tz import now
from kubernetes.client.rest import ApiException

from polyaxon._k8s.manager.manager import K8sManager
from polyaxon.client import RunClient
from polyaxon.exceptions import PolyaxonK8sError
from traceml.logging import V1Log


def query_logs(
    k8s_manager: K8sManager,
    pod_id: str,
    container_id: str,
    stream: bool = False,
    since_seconds: Optional[int] = None,
) -> Any:
    params: Dict[str, Any] = {}
    if stream:
        params = {"follow": True, "_preload_content": False}
    if since_seconds:
        params = {"since_seconds": since_seconds}

    return k8s_manager.k8s_api.read_namespaced_pod_log(
        pod_id, k8s_manager.namespace, container=container_id, timestamps=True, **params
    )


def process_log_line(log_line: str):
    if not isinstance(log_line, str):
        log_line = log_line.decode("utf-8")

    return V1Log.process_log_line(
        value=log_line.strip(), node=None, pod=None, container=None
    )


def stream_logs(
    k8s_manager: K8sManager, pod_id: str, container_id: str
) -> Iterable[str]:
    raw = None
    retries = 0
    no_logs = True

    while retries < 3 and no_logs:
        try:
            raw = query_logs(
                k8s_manager=k8s_manager,
                pod_id=pod_id,
                container_id=container_id,
                stream=True,
            )
        except (PolyaxonK8sError, ApiException):
            retries += 1

    if not raw:
        yield ""
    else:
        for log_line in raw.stream():
            if log_line:
                yield process_log_line(log_line=log_line)


def process_logs(
    k8s_manager: K8sManager,
    pod_id: str,
    container_id: str,
    filepath: str,
    since_seconds: Optional[int],
) -> bool:
    logs = None
    retries = 0
    no_logs = True
    while retries < 3 and no_logs:
        try:
            logs = query_logs(
                k8s_manager=k8s_manager,
                pod_id=pod_id,
                container_id=container_id,
                since_seconds=since_seconds,
            )
            no_logs = False
        except (PolyaxonK8sError, ApiException):
            retries += 1

    if not logs:
        return False

    log_lines = []
    for log_line in logs.split("\n"):
        if log_line:
            log_lines.append(process_log_line(log_line=log_line))

    # Creating the new file
    if not log_lines:
        return False

    with open(filepath, "w+") as destination:
        destination.write("\n".join(log_lines))

    return True


def sync_logs(
    k8s_manager: K8sManager,
    client: RunClient,
    last_check: Optional[datetime],
    pod_id: str,
    container_id: str,
    owner: str,
    project: str,
    run_uuid: str,
):
    new_check = now()
    since_seconds = None
    if last_check:
        since_seconds = (new_check - last_check).total_seconds()

        if since_seconds < 1:
            return last_check

    filepath = str(new_check.timestamp())
    created = process_logs(
        k8s_manager=k8s_manager,
        pod_id=pod_id,
        container_id=container_id,
        since_seconds=since_seconds,
        filepath=filepath,
    )
    if created:
        client.client.upload_run_logs(
            owner, project, run_uuid, uploadfile=filepath, path=filepath
        )
        return new_check

    return last_check
