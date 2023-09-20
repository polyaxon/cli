from typing import Dict, Union

from polyaxon._k8s import k8s_schemas


def has_tpu_annotation(annotations: Dict) -> bool:
    if not annotations:
        return False
    for key in annotations.keys():
        if "tpu" in key:
            return True

    return False


def requests_tpu(resources: Union[k8s_schemas.V1ResourceRequirements, Dict]) -> bool:
    if not resources:
        return False

    if not isinstance(resources, k8s_schemas.V1ResourceRequirements):
        resources = k8s_schemas.V1ResourceRequirements(**resources)

    if resources.requests:
        for key in resources.requests.keys():
            if "tpu" in key:
                return True

    if resources.limits:
        for key in resources.limits.keys():
            if "tpu" in key:
                return True

    return False


def requests_gpu(resources: k8s_schemas.V1ResourceRequirements) -> bool:
    if not resources:
        return False

    if resources.requests:
        for key in resources.requests.keys():
            if "gpu" in key:
                return True

    if resources.limits:
        for key in resources.limits.keys():
            if "gpu" in key:
                return True

    return False
