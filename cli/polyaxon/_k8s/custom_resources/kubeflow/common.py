from typing import Dict, Optional

from polyaxon._k8s.converter.pod.spec import get_pod_spec, get_pod_template_spec
from polyaxon._k8s.replica import ReplicaSpec


def get_kf_replicas_template(
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
