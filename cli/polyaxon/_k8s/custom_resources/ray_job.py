from typing import Dict, List, Optional

from polyaxon._flow import V1Notification, V1Termination
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.pod.spec import get_pod_spec, get_pod_template_spec
from polyaxon._k8s.custom_resources.operation import get_operation_custom_object
from polyaxon._k8s.custom_resources.setter import (
    set_collect_logs,
    set_notify,
    set_sync_statuses,
    set_termination,
)
from polyaxon._k8s.replica import ReplicaSpec


def _get_ray_replicas_template(
    namespace: str,
    resource_name: str,
    replica_name: Optional[str],
    replica: Optional[ReplicaSpec],
    labels: Dict[str, str],
    annotations: Dict[str, str],
    template_spec: Dict,
    default_start_params: Optional[Dict] = None,
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

    data = {
        "replicas": replica.num_replicas,
        "restartPolicy": pod_spec.restart_policy or "Never",
        "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec),
    }
    custom = replica.custom or {}
    if custom.get("min_replicas"):
        data["minReplicas"] = custom["min_replicas"]
    if custom.get("max_replicas"):
        data["maxReplicas"] = custom["max_replicas"]
    if custom.get("ray_start_params"):
        data["rayStartParams"] = custom["ray_start_params"]
    if default_start_params:
        data["rayStartParams"] = {
            **default_start_params,
            **data.get("rayStartParams", {}),
        }
    if replica_name:
        data["groupName"] = replica_name
    return data


def get_ray_head_replicas_template(
    namespace: str,
    resource_name: str,
    replica: Optional[ReplicaSpec],
    labels: Dict[str, str],
    annotations: Dict[str, str],
    template_spec: Dict,
):
    if replica:
        # Set default ports on main container
        if not replica.main_container.ports:
            replica.main_container.ports = [
                k8s_schemas.V1ContainerPort(
                    container_port=6379, name="gcs-server", protocol="TCP"
                ),
                k8s_schemas.V1ContainerPort(
                    container_port=8265, name="dashboard", protocol="TCP"
                ),
                k8s_schemas.V1ContainerPort(
                    container_port=10001, name="client", protocol="TCP"
                ),
                k8s_schemas.V1ContainerPort(
                    container_port=8000, name="serve", protocol="TCP"
                ),
            ]
    head = _get_ray_replicas_template(
        namespace=namespace,
        resource_name=resource_name,
        replica_name="head",
        replica=replica,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
        default_start_params={"dashboard-host": "0.0.0.0"},
    )
    if head:
        template_spec["head"] = head


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
        worker = _get_ray_replicas_template(
            namespace=namespace,
            resource_name=resource_name,
            replica_name=replica_name,
            replica=replica,
            labels=labels,
            annotations=annotations,
            template_spec=template_spec,
        )
        # Check the lifecycle is set
        if worker:
            template = worker["template"]
            if template.spec.containers[0].lifecycle is None:
                template.spec.containers[0].lifecycle = {
                    "preStop": {"exec": {"command": ["/bin/sh", "-c", "ray stop"]}}
                }
                worker["template"] = template
            workers.append(worker)
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

    get_ray_head_replicas_template(
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
