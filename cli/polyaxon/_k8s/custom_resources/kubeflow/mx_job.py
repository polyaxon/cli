from typing import Dict, List, Optional

from polyaxon._flow import V1Notification, V1SchedulingPolicy, V1Termination
from polyaxon._k8s.custom_resources.kubeflow.common import get_kf_replicas_template
from polyaxon._k8s.custom_resources.operation import get_operation_custom_object
from polyaxon._k8s.custom_resources.setter import (
    set_clean_pod_policy,
    set_collect_logs,
    set_notify,
    set_scheduling_policy,
    set_sync_statuses,
    set_termination,
)
from polyaxon._k8s.replica import ReplicaSpec


def get_mx_job_custom_resource(
    resource_name: str,
    namespace: str,
    scheduler: Optional[ReplicaSpec],
    server: Optional[ReplicaSpec],
    worker: Optional[ReplicaSpec],
    tuner: Optional[ReplicaSpec],
    tuner_tracker: Optional[ReplicaSpec],
    tuner_server: Optional[ReplicaSpec],
    termination: V1Termination,
    collect_logs: bool,
    sync_statuses: bool,
    notifications: List[V1Notification],
    clean_pod_policy: Optional[str],
    scheduling_policy: Optional[V1SchedulingPolicy],
    mode: Optional[str],
    labels: Dict[str, str],
    annotations: Dict[str, str],
) -> Dict:
    template_spec = {}

    get_kf_replicas_template(
        replica_name="Scheduler",
        replica=scheduler,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_kf_replicas_template(
        replica_name="Server",
        replica=server,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_kf_replicas_template(
        replica_name="Worker",
        replica=worker,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_kf_replicas_template(
        replica_name="Tuner",
        replica=tuner,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_kf_replicas_template(
        replica_name="TunerTracker",
        replica=tuner_tracker,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_kf_replicas_template(
        replica_name="TunerServer",
        replica=tuner_server,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    template_spec = {"replicaSpecs": template_spec}

    template_spec = set_clean_pod_policy(
        template_spec=template_spec, clean_pod_policy=clean_pod_policy
    )

    template_spec = set_scheduling_policy(
        template_spec=template_spec, scheduling_policy=scheduling_policy
    )

    if mode:
        template_spec["jobMode"] = mode

    custom_object = {"mxJobSpec": template_spec}
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
