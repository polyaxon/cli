from typing import Dict

from polyaxon._k8s import k8s_schemas


def get_custom_object(
    namespace: str,
    resource_name: str,
    kind: str,
    api_version: str,
    labels: Dict,
    annotations: Dict,
    custom_object: Dict,
) -> Dict:
    metadata = k8s_schemas.V1ObjectMeta(
        name=resource_name,
        labels=labels,
        annotations=annotations,
        namespace=namespace,
    )
    custom_object.update(
        {"kind": kind, "apiVersion": api_version, "metadata": metadata}
    )

    return custom_object
