from typing import Dict

from polyaxon._k8s.custom_resources.crd import get_custom_object

KIND = "Operation"
PLURAL = "operations"
JOB_KIND = "Job"
JOB_PLURAL = "jobs"
SERVICES_KIND = "Service"
SERVICES_PLURAL = "services"
CLUSTER_KIND = "Cluster"
CLUSTER_PLURAL = "clusters"
KFJOB_KIND = "KfJob"
KFJOB_PLURAL = "kfjobs"
API_VERSION = "v1"
GROUP = "polyaxon.com"


def get_operation_custom_object(
    resource_name: str,
    namespace: str,
    kind: str,
    custom_object: Dict,
    annotations: Dict[str, str],
    labels: Dict[str, str],
) -> Dict:
    return get_custom_object(
        resource_name=resource_name,
        namespace=namespace,
        kind=kind,
        api_version="{}/{}".format(GROUP, API_VERSION),
        labels=labels,
        annotations=annotations,
        custom_object=custom_object,
    )
