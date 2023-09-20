from polyaxon._k8s.events import get_container_status, get_container_statuses_by_name
from polyaxon._k8s.pods import PodLifeCycle


def is_container_terminated(status, container_id):
    container_statuses = status.get("container_statuses") or []
    statuses_by_name = get_container_statuses_by_name(container_statuses)
    statuses = get_container_status(statuses_by_name, (container_id,))
    statuses = statuses or {}
    return statuses.get("state", {}).get("terminated")


def is_pod_running(event, container_id):
    event = event.to_dict()
    event_status = event.get("status", {})
    is_terminated = is_container_terminated(
        status=event_status, container_id=container_id
    )

    return (
        event_status.get("phase")
        in {PodLifeCycle.RUNNING, PodLifeCycle.PENDING, PodLifeCycle.CONTAINER_CREATING}
        and not is_terminated
    )
