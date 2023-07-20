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


def _get_ray_replicas_template(
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

    return {
        "replicas": replica.num_replicas,
        "restartPolicy": pod_spec.restart_policy or "Never",
        "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec),
    }


def get_ray_replicas_template(
    namespace: str,
    resource_name: str,
    replica_name: str,
    replica: Optional[ReplicaSpec],
    labels: Dict[str, str],
    annotations: Dict[str, str],
    template_spec: Dict,
):
    template = _get_ray_replicas_template(
        namespace=namespace,
        resource_name=resource_name,
        replica_name=replica_name,
        replica=replica,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    if template:
        template_spec[replica_name] = template


def get_ray_worker_replicas_template(
    namespace: str,
    resource_name: str,
    replicas: Optional[Dict[str, ReplicaSpec]],
    labels: Dict[str, str],
    annotations: Dict[str, str],
    template_spec: Dict,
):
    workers = []
    for replica_name in replicas or {}:
        replica = replicas[replica_name]
        workers.append(
            _get_ray_replicas_template(
                namespace=namespace,
                resource_name=resource_name,
                replica_name=replica_name,
                replica=replica,
                labels=labels,
                annotations=annotations,
                template_spec=template_spec,
            )
        )
    if workers:
        template_spec["workers"] = workers


def get_ray_job_custom_resource(
    resource_name: str,
    namespace: str,
    head: Optional[ReplicaSpec],
    workers: Optional[Dict[str, ReplicaSpec]],
    termination: V1Termination,
    collect_logs: bool,
    sync_statuses: bool,
    notifications: List[V1Notification],
    entrypoint: Optional[str],
    metadata: Optional[Dict[str, str]],
    runtime_env: Optional[str],
    ray_version: Optional[str],
    labels: Dict[str, str],
    annotations: Dict[str, str],
) -> Dict:
    template_spec = {}

    get_ray_replicas_template(
        replica_name="head",
        replica=head,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_ray_worker_replicas_template(
        replicas=workers,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    if entrypoint:
        template_spec["entrypoint"] = entrypoint
    if metadata:
        template_spec["metadata"] = metadata
    if runtime_env:
        template_spec["runtimeEnv"] = runtime_env
    if ray_version:
        template_spec["rayVersion"] = ray_version

    custom_object = {"rayJobSpec": template_spec}
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
