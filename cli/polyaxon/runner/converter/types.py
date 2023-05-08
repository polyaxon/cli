from typing import Dict, List, Union

from polyaxon.docker import docker_types
from polyaxon.k8s import k8s_schemas

EnvVar = Union[k8s_schemas.V1EnvVar, docker_types.V1EnvVar]
Container = Union[k8s_schemas.V1Container, docker_types.V1Container]
Resource = Union[Dict, List[docker_types.V1Container]]
