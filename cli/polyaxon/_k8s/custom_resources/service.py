from typing import Dict, List, Optional

from polyaxon._flow import V1Environment, V1Notification, V1Termination
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.pod.spec import get_pod_spec, get_pod_template_spec
from polyaxon._k8s.custom_resources.operation import get_operation_custom_object
from polyaxon._k8s.custom_resources.setter import (
    set_collect_logs,
    set_notify,
    set_sync_statuses,
    set_termination,
)


def get_service_custom_resource(
    resource_name: str,
    namespace: str,
    main_container: k8s_schemas.V1Container,
    sidecar_containers: Optional[List[k8s_schemas.V1Container]],
    init_containers: Optional[List[k8s_schemas.V1Container]],
    volumes: List[k8s_schemas.V1Volume],
    termination: V1Termination,
    collect_logs: bool,
    sync_statuses: bool,
    notifications: List[V1Notification],
    environment: V1Environment,
    ports: List[int],
    replicas: Optional[int],
    is_external: bool,
    labels: Dict[str, str],
    annotations: Dict[str, str],
) -> Dict:
    metadata, pod_spec = get_pod_spec(
        namespace=namespace,
        main_container=main_container,
        sidecar_containers=sidecar_containers,
        init_containers=init_containers,
        resource_name=resource_name,
        volumes=volumes,
        environment=environment,
        labels=labels,
        annotations=annotations,
    )

    template_spec = {
        "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec)
    }

    if ports:
        template_spec["ports"] = ports

    if replicas is not None:
        template_spec["replicas"] = replicas

    if is_external:
        template_spec["isExternal"] = is_external

    custom_object = {"serviceSpec": template_spec}
    custom_object = set_termination(
        custom_object=custom_object, termination=termination
    )
    custom_object = set_collect_logs(
        custom_object=custom_object, collect_logs=collect_logs
    )
    custom_object = set_sync_statuses(
        custom_object=custom_object, sync_statuses=sync_statuses
    )
    custom_object = set_notify(custom_object=custom_object, notifications=notifications)

    return get_operation_custom_object(
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        custom_object=custom_object,
    )
