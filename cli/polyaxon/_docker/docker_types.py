from typing import Dict, List, Optional, Tuple, Union

from clipped.compact.pydantic import (
    PYDANTIC_VERSION,
    Field,
    field_validator,
    validation_always,
)
from clipped.utils.units import to_cpu_value, to_memory_bytes, to_unit_memory

from polyaxon._schemas.base import BaseSchemaModel, RootModel


class V1EnvVar(RootModel):
    if PYDANTIC_VERSION.startswith("2."):
        root: Union[Tuple[str, str], Dict[str, str]]
    else:
        __root__: Union[Tuple[str, str], Dict[str, str]]

    def to_cmd(self):
        value = self.get_root()
        return [f"{value[0]}={value[1]}"]


class V1VolumeMount(RootModel):
    if PYDANTIC_VERSION.startswith("2."):
        root: Tuple[str, str]
    else:
        __root__: Tuple[str, str]

    def to_cmd(self):
        return list(self.get_root())


ROOT_TYPE = Union[
    int,
    str,
    List[Union[int, str]],
    Tuple[Union[int, str], Union[int, str]],
    Dict[Union[int, str], Union[Union[int, str], Union[int, str]]],
]


class V1ContainerPort(RootModel):
    if PYDANTIC_VERSION.startswith("2."):
        root: ROOT_TYPE
    else:
        __root__: ROOT_TYPE

    def to_cmd(self):
        root = self.get_root()
        if isinstance(root, (str, int)):
            return [root]

        if isinstance(root, (list, tuple)):
            value = root
        else:
            value = root.items()
        return list(value[0])


class V1ResourceRequirements(BaseSchemaModel):
    cpus: Optional[Union[str, float, int]] = None
    memory: Optional[Union[str, float, int]] = None
    gpus: Optional[str] = None

    @field_validator("cpus", "memory", **validation_always)
    def value_to_str(cls, v):
        return str(v)

    @staticmethod
    def from_k8s_cpu(cpu: str) -> Union[str, float]:
        if not cpu:
            return cpu
        return to_cpu_value(cpu)

    @staticmethod
    def from_k8s_memory(memory: str) -> str:
        if not memory:
            return memory
        docker_mem_bytes = to_memory_bytes(memory)
        return to_unit_memory(number=docker_mem_bytes, use_i=False, use_space=False)

    def to_cmd(self):
        cmd_args = []
        if self.cpus:
            cmd_args += ["--cpus", self.cpus]
        if self.memory:
            cmd_args += ["--memory", self.memory]
        if self.gpus:
            cmd_args += ["--gpus", self.gpus]
        return cmd_args


class V1Container(BaseSchemaModel):
    image: Optional[str] = None
    name: Optional[str] = None
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    env: Optional[List[V1EnvVar]] = None
    volume_mounts: Optional[List[V1VolumeMount]] = Field(
        alias="volumeMounts", default=None
    )
    resources: Optional[V1ResourceRequirements] = None
    ports: Optional[List[V1ContainerPort]] = None
    working_dir: Optional[str] = Field(alias="workingDir", default=None)

    def get_cmd_args(self):
        cmd_args = ["run", "--rm"]
        for env in self.env:
            cmd_args += ["-e"] + env.to_cmd()
        for volume in self.volume_mounts:
            cmd_args += volume.to_cmd()
        if self.working_dir:
            cmd_args += ["-w", self.working_dir]
        if self.resources:
            if self.resources.cpus:
                cmd_args += ["--cpus", self.resources.cpus]
            if self.resources.memory:
                cmd_args += ["--memory", self.resources.memory]
            if self.resources.gpus:
                cmd_args += ["--gpus", self.resources.gpus]
        if self.ports:
            for port in self.ports:
                cmd_args += ["-p"] + port.to_cmd()
        if self.command:
            cmd_args += ["--entrypoint", self.command[0]]
        cmd_args += [self.image]
        if self.command:
            cmd_args += self.command[1:]
        if self.args:
            cmd_args += self.args
        return cmd_args
