from typing import Dict

from polyaxon._k8s.custom_resources.crd import get_custom_object

KIND = "Operation"
PLURAL = "operations"
API_VERSION = "v1"
GROUP = "core.polyaxon.com"


def get_operation_custom_object(
    resource_name: str,
    namespace: str,
    custom_object: Dict,
    annotations: Dict[str, str],
    labels: Dict[str, str],
) -> Dict:
    return get_custom_object(
        resource_name=resource_name,
        namespace=namespace,
        kind=KIND,
        api_version="{}/{}".format(GROUP, API_VERSION),
        labels=labels,
        annotations=annotations,
        custom_object=custom_object,
    )
