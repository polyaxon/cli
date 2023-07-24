from typing import Dict, List, Optional

from kubernetes import client

from polyaxon.k8s import k8s_schemas
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


def get_dask_replicas_template(
    namespace: str,
    resource_name: str,
    replica_name: str,
    replica: Optional[ReplicaSpec],
    labels: Dict[str, str],
    annotations: Dict[str, str],
    template_spec: Dict,
    args: Optional[List[str]] = None,
    ports: Optional[List[k8s_schemas.V1ContainerPort]] = None,
    readiness_probe: Optional[client.V1Probe] = None,
    liveness_probe: Optional[client.V1Probe] = None,
):
    if not replica:
        return

    if ports and replica.main_container.ports is None:
        replica.main_container.ports = ports
    if args and replica.main_container.args is None:
        replica.main_container.args = args
    if readiness_probe and replica.main_container.readiness_probe is None:
        replica.main_container.readiness_probe = readiness_probe
    if liveness_probe and replica.main_container.liveness_probe is None:
        replica.main_container.liveness_probe = liveness_probe

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


def get_dask_job_custom_resource(
    resource_name: str,
    namespace: str,
    job: Optional[ReplicaSpec],
    worker: Optional[ReplicaSpec],
    scheduler: Optional[ReplicaSpec],
    termination: V1Termination,
    collect_logs: bool,
    sync_statuses: bool,
    notifications: List[V1Notification],
    labels: Dict[str, str],
    annotations: Dict[str, str],
) -> Dict:
    template_spec = {}

    get_dask_replicas_template(
        replica_name="Job",
        replica=job,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
    )
    get_dask_replicas_template(
        replica_name="Worker",
        replica=worker,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
        args=[
            "dask-worker",
            "--name",
            "$(DASK_WORKER_NAME)",
            "--dashboard",
            "--dashboard-address",
            "8788",
        ],
        ports=[
            k8s_schemas.V1ContainerPort(
                name="http-dashboard", container_port=8788, protocol="TCP"
            )
        ],
    )
    get_dask_replicas_template(
        replica_name="Scheduler",
        replica=scheduler,
        namespace=namespace,
        resource_name=resource_name,
        labels=labels,
        annotations=annotations,
        template_spec=template_spec,
        args=["dask-scheduler", "--dashboard", "--dashboard-address", "8787"],
        ports=[
            k8s_schemas.V1ContainerPort(
                name="tcp-comm", container_port=8786, protocol="TCP"
            ),
            k8s_schemas.V1ContainerPort(
                name="http-dashboard", container_port=8787, protocol="TCP"
            ),
        ],
        readiness_probe=client.V1Probe(
            http_get=client.V1HTTPGetAction(path="/", port="http-dashboard"),
            initial_delay_seconds=5,
            period_seconds=5,
        ),
        liveness_probe=client.V1Probe(
            http_get=client.V1HTTPGetAction(path="/", port="http-dashboard"),
            initial_delay_seconds=15,
            period_seconds=15,
        ),
    )
    service = client.V1ServiceSpec(
        type="ClusterIP",
        selector={
            **labels,
            "dask.org/cluster-name": resource_name,
            "dask.org/component": "scheduler",
        },
        ports=[
            client.V1ServicePort(
                port=8786, target_port="tcp-comm", name="tcp-comm", protocol="TCP"
            ),
            client.V1ServicePort(
                port=8787,
                target_port="http-dashboard",
                name="http-dashboard",
                protocol="TCP",
            ),
        ],
    )
    template_spec = {"replicaSpecs": template_spec, "service": service}
    custom_object = {"daskJobSpec": template_spec}
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
