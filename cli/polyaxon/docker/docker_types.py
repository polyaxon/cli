from typing import Dict, List, Optional, Tuple, Union

from pydantic import Field

from polyaxon.schemas.base import BaseSchemaModel


class V1EnvVar(BaseSchemaModel):
    __root__: Union[Tuple[str, str], Dict[str, str]]


class V1VolumeMount(BaseSchemaModel):
    __root__: Union[Tuple[str, str], Dict[str, str]]


class V1ContainerPort(BaseSchemaModel):
    __root__: Union[str, Tuple[str, str], Dict[str, str]]


class V1ResourceRequirements(BaseSchemaModel):
    cpus: Optional[str]
    memory: Optional[str]
    gpus: Optional[str]


class V1Container(BaseSchemaModel):
    image: Optional[str]
    name: Optional[str]
    command: Optional[List[str]]
    args: Optional[List[str]]
    env: Optional[List[V1EnvVar]]
    volume_mounts: Optional[List[V1VolumeMount]] = Field(alias="volumeMounts")
    resources: Optional[V1ResourceRequirements]
    ports: Optional[List[V1ContainerPort]]
    working_dir: Optional[str] = Field(alias="workingDir")
