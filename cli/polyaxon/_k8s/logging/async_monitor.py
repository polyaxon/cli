import datetime
import logging

from typing import List, Optional, Tuple

from clipped.utils.tz import now
from kubernetes_asyncio.client.models import V1Pod
from kubernetes_asyncio.client.rest import ApiException

from polyaxon._flow import V1RunKind
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from traceml.logging import V1Log, V1Logs

_logger = logging.getLogger("haupt.k8s.logs")


async def handle_container_logs(
    k8s_manager: AsyncK8sManager, pod: V1Pod, container_name: str, **params
) -> List[V1Log]:
    resp = None
    try:
        resp = await k8s_manager.k8s_api.read_namespaced_pod_log(
            pod.metadata.name,
            k8s_manager.namespace,
            container=container_name,
            timestamps=True,
            **params,
        )
    except ApiException as e:
        _logger.warning(
            "Error collecting logs for %s - container %s: %s",
            pod.metadata.name,
            container_name,
            e,
        )
    except Exception as e:
        _logger.warning(
            "Unexpected error collecting logs for %s - container %s: %s",
            pod.metadata.name,
            container_name,
            e,
        )
    if not resp:
        return []

    logs = []
    for log_line in resp.split("\n"):
        if log_line:
            logs.append(
                V1Log.process_log_line(
                    value=log_line,
                    node=pod.spec.node_name,
                    pod=pod.metadata.name,
                    container=container_name,
                )
            )
    return logs


async def handle_pod_logs(
    k8s_manager: AsyncK8sManager, pod: V1Pod, **params
) -> List[V1Log]:
    logs = []
    for container in pod.spec.init_containers or []:
        logs += await handle_container_logs(
            k8s_manager=k8s_manager, pod=pod, container_name=container.name, **params
        )
    for container in pod.spec.containers or []:
        logs += await handle_container_logs(
            k8s_manager=k8s_manager, pod=pod, container_name=container.name, **params
        )
    return logs


async def query_k8s_operation_logs(
    k8s_manager: AsyncK8sManager,
    instance: str,
    last_time: Optional[datetime.datetime],
    stream: bool = False,
) -> Tuple[List[V1Log], Optional[datetime.datetime]]:
    new_time = now()
    params = {}
    if last_time:
        since_seconds = (new_time - last_time).total_seconds()
        params["since_seconds"] = int(since_seconds)
    if stream:
        params["tail_lines"] = V1Logs._CHUNK_SIZE
    logs = []

    pods = await k8s_manager.list_pods(
        label_selector=k8s_manager.get_managed_by_polyaxon(instance)
    )

    for pod in pods:
        logs += await handle_pod_logs(
            k8s_manager=k8s_manager,
            pod=pod,
            **params,
        )

    if logs and last_time:
        # make sure to filter logs larger than last_time
        logs = [log for log in logs if log.timestamp > last_time]
    if logs and logs[-1].timestamp:
        new_time = logs[-1].timestamp
    return logs, new_time


async def collect_agent_service_logs(
    k8s_manager: AsyncK8sManager, pod: V1Pod
) -> List[V1Log]:
    if not pod or not pod.spec.containers:
        return []
    container = pod.spec.containers[0]
    return await handle_container_logs(
        k8s_manager=k8s_manager,
        pod=pod,
        container_name=container.name,
        tail_lines=V1Logs._CHUNK_SIZE,
    )


async def query_k8s_pod_logs(
    k8s_manager: AsyncK8sManager,
    pod: V1Pod,
    last_time: Optional[datetime.datetime] = None,
    stream: bool = False,
) -> Tuple[List[V1Log], Optional[datetime.datetime]]:
    new_time = now()
    params = {}
    if last_time:
        since_seconds = (new_time - last_time).total_seconds()
        params["since_seconds"] = int(since_seconds)
    if stream:
        params["tail_lines"] = V1Logs._CHUNK_SIZE

    logs = await handle_pod_logs(k8s_manager=k8s_manager, pod=pod, **params)

    if logs and last_time:
        # make sure to filter logs larger than last_time
        logs = [log for log in logs if log.timestamp > last_time]
    if logs and logs[-1].timestamp:
        new_time = logs[-1].timestamp
    return logs, new_time


async def get_op_pods_and_services(
    k8s_manager: AsyncK8sManager,
    run_uuid: str,
    run_kind: str,
):
    pods = await k8s_manager.list_pods(
        label_selector=k8s_manager.get_managed_by_polyaxon(run_uuid)
    )
    services = []
    if V1RunKind.has_service(run_kind):
        services = await k8s_manager.list_services(
            label_selector=k8s_manager.get_managed_by_polyaxon(run_uuid)
        )

    return pods, services


async def get_resource_events(
    k8s_manager: AsyncK8sManager, resource_type: str, resource_name: str
):
    field_selector = (
        f"involvedObject.kind={resource_type},involvedObject.name={resource_name}"
    )
    try:
        events = await k8s_manager.list_namespaced_events(field_selector=field_selector)

        all_events = []
        for event in events:
            event_data = {
                "reason": event.reason,
                "message": event.message,
                "first_timestamp": event.first_timestamp,
                "last_timestamp": event.last_timestamp,
                "count": event.count,
                "type": event.type,
            }
            all_events.append(event_data)

        return all_events

    except ApiException as e:
        print(f"Exception when calling CoreV1Api->list_namespaced_event: {e}")
        return []


async def get_op_spec(
    k8s_manager: AsyncK8sManager,
    run_uuid: str,
    run_kind: str,
):
    pods, services = await get_op_pods_and_services(
        k8s_manager=k8s_manager,
        run_uuid=run_uuid,
        run_kind=run_kind,
    )
    pods_list = {}
    for pod in pods or []:
        pods_list[
            pod.metadata.name
        ] = k8s_manager.api_client.sanitize_for_serialization(pod)  # fmt: skip
        pods_list[pod.metadata.name]["events"] = await get_resource_events(
            k8s_manager=k8s_manager,
            resource_type="Pod",
            resource_name=pod.metadata.name,
        )
    services_list = {}
    for service in services or []:
        services_list[
            service.metadata.name
        ] = k8s_manager.api_client.sanitize_for_serialization(service)  # fmt: skip
        services_list[service.metadata.name]["events"] = await get_resource_events(
            k8s_manager=k8s_manager,
            resource_type="Service",
            resource_name=service.metadata.name,
        )
    data = {"pods": pods_list, "services": services_list}
    return data, pods, services


async def get_agent_pods_and_services(
    k8s_manager: AsyncK8sManager,
):
    pods = await k8s_manager.list_pods(
        label_selector=k8s_manager.get_core_polyaxon(),
    )
    services = await k8s_manager.list_services(
        label_selector=k8s_manager.get_core_polyaxon(),
    )
    return pods, services


async def get_agent_spec(
    k8s_manager: AsyncK8sManager,
):
    pods, services = await get_agent_pods_and_services(
        k8s_manager=k8s_manager,
    )
    pods_list = {}
    for pod in pods or []:
        pods_list[
            pod.metadata.name
        ] = k8s_manager.api_client.sanitize_for_serialization(pod)  # fmt: skip
        pods_list[pod.metadata.name]["events"] = await get_resource_events(
            k8s_manager=k8s_manager,
            resource_type="Pod",
            resource_name=pod.metadata.name,
        )
    data = {"pods": pods_list}
    services_list = {}
    for service in services or []:
        services_list[
            service.metadata.name
        ] = k8s_manager.api_client.sanitize_for_serialization(service)  # fmt: skip
        services_list[service.metadata.name]["events"] = await get_resource_events(
            k8s_manager=k8s_manager,
            resource_type="Service",
            resource_name=service.metadata.name,
        )
    data["services"] = services_list
    return data, pods, services
