from typing import Dict, List, Optional, Tuple

from clipped.utils.lists import to_list
from clipped.utils.sanitizers import sanitize_string_dict

from polyaxon._flow import V1Environment
from polyaxon._k8s import k8s_schemas
from polyaxon.exceptions import PolyaxonConverterError


def get_pod_spec(
    resource_name: str,
    namespace: str,
    main_container: k8s_schemas.V1Container,
    sidecar_containers: Optional[List[k8s_schemas.V1Container]],
    init_containers: Optional[List[k8s_schemas.V1Container]],
    environment: Optional[V1Environment],
    labels: Dict[str, str],
    annotations: Dict[str, str],
    volumes: Optional[List[k8s_schemas.V1Volume]],
) -> Tuple[k8s_schemas.V1ObjectMeta, k8s_schemas.V1PodSpec]:
    if not main_container:
        raise PolyaxonConverterError("A main container is required")
    environment = environment or V1Environment()

    metadata = k8s_schemas.V1ObjectMeta(
        name=resource_name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
    )

    init_containers = to_list(init_containers, check_none=True)
    containers = [main_container] + to_list(sidecar_containers, check_none=True)
    image_pull_secrets = None
    if environment.image_pull_secrets:
        image_pull_secrets = [
            k8s_schemas.V1LocalObjectReference(name=i)
            for i in environment.image_pull_secrets
        ]

    pod_spec = k8s_schemas.V1PodSpec(
        init_containers=init_containers,
        containers=containers,
        volumes=volumes,
        restart_policy=environment.restart_policy,
        image_pull_secrets=image_pull_secrets,
        security_context=environment.security_context,
        service_account_name=environment.service_account_name,
        node_selector=sanitize_string_dict(environment.node_selector),
        tolerations=environment.tolerations,
        affinity=environment.affinity,
        dns_config=environment.dns_config,
        dns_policy=environment.dns_policy,
        host_aliases=environment.host_aliases,
        host_network=environment.host_network,
        host_pid=str(environment.host_pid)
        if environment.host_pid is not None
        else environment.host_pid,
        node_name=environment.node_name,
        priority=environment.priority,
        priority_class_name=environment.priority_class_name,
        scheduler_name=environment.scheduler_name,
    )
    return metadata, pod_spec


def get_pod_template_spec(
    metadata: k8s_schemas.V1ObjectMeta, pod_spec: k8s_schemas.V1PodSpec
) -> k8s_schemas.V1PodTemplateSpec:
    return k8s_schemas.V1PodTemplateSpec(metadata=metadata, spec=pod_spec)
