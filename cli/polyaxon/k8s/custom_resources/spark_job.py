from typing import Dict, List, Optional

from polyaxon.k8s.converter.pod.spec import get_pod_spec, get_pod_template_spec
from polyaxon.k8s.custom_resources.operation import get_operation_custom_object
from polyaxon.k8s.custom_resources.setter import (
    set_collect_logs,
    set_notify,
    set_sync_statuses,
    set_termination,
)
from polyaxon.k8s.replica import ReplicaSpec
from polyaxon.polyflow import V1Notification, V1Termination


def get_spark_replicas_template(
    namespace: str,
    resource_name: str,
    replica_name: str,
    replica: Optional[ReplicaSpec],
    labels: Dict[str, str],
    annotations: Dict[str, str],
    template_spec: Dict,
):
    if not replica:
        return

    metadata, pod_spec = get_pod_spec(
        namespace=namespace,
        main_container=replica.main_container,
        sidecar_containers=replica.sidecar_containers,
        init_containers=replica.init_containers,
        resource_name=resource_name,
        volumes=replica.volumes,
        environment=replica.environment,
        labels=labels,
        annotations=annotations,
    )

    template_spec[replica_name] = {
        "replicas": replica.num_replicas,
        "restartPolicy": pod_spec.restart_policy or "Never",
        "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec),
    }


def get_spark_job_custom_resource(
    resource_name: str,
    namespace: str,
    executor: Optional[ReplicaSpec],
    driver: Optional[ReplicaSpec],
    termination: V1Termination,
    collect_logs: bool,
    sync_statuses: bool,
    notifications: List[V1Notification],
    labels: Dict[str, str],
    annotations: Dict[str, str],
) -> Dict:
    template_spec = {}

    get_spark_replicas_template(
        replica_name="Executor",
        replica=executor,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_spark_replicas_template(
        replica_name="Driver",
        replica=driver,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    template_spec = {"replicaSpecs": template_spec}
    custom_object = {"sparkJobSpec": template_spec}
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
