from typing import Dict, List, Union

from polyaxon._docker import docker_types
from polyaxon._k8s import k8s_schemas

EnvVar = Union[k8s_schemas.V1EnvVar, docker_types.V1EnvVar]
ResourceRequirements = Union[
    k8s_schemas.V1ResourceRequirements, docker_types.V1ResourceRequirements
]
Container = Union[k8s_schemas.V1Container, docker_types.V1Container]
ContainerPort = Union[k8s_schemas.V1ContainerPort, docker_types.V1ContainerPort]
Resource = Union[Dict, List[docker_types.V1Container]]
VolumeMount = Union[k8s_schemas.V1VolumeMount, docker_types.V1VolumeMount]
