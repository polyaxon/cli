from typing import Dict, List, Optional, Tuple, Union

from clipped.compact.pydantic import Field
from clipped.utils.units import to_cpu_value, to_memory_bytes, to_unit_memory

from polyaxon._schemas.base import BaseSchemaModel


class V1EnvVar(BaseSchemaModel):
    __root__: Union[Tuple[str, str], Dict[str, str]]

    def to_cmd(self):
        if isinstance(self.__root__, tuple):
            value = self.__root__
        else:
            value = self.__root__.items()
        return [f"{value[0]}={value[1]}"]


class V1VolumeMount(BaseSchemaModel):
    __root__: Tuple[str, str]

    def to_cmd(self):
        return list(self.__root__)


class V1ContainerPort(BaseSchemaModel):
    __root__: Union[str, Tuple[str, str], Dict[str, str]]

    def to_cmd(self):
        if isinstance(self.__root__, str):
            return [self.__root__]

        if isinstance(self.__root__, tuple):
            value = self.__root__
        else:
            value = self.__root__.items()
        return list(value[0])


class V1ResourceRequirements(BaseSchemaModel):
    cpus: Optional[str]
    memory: Optional[str]
    gpus: Optional[str]

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
    image: Optional[str]
    name: Optional[str]
    command: Optional[List[str]]
    args: Optional[List[str]]
    env: Optional[List[V1EnvVar]]
    volume_mounts: Optional[List[V1VolumeMount]] = Field(alias="volumeMounts")
    resources: Optional[V1ResourceRequirements]
    ports: Optional[List[V1ContainerPort]]
    working_dir: Optional[str] = Field(alias="workingDir")

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
