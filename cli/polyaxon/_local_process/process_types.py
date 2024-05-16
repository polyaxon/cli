from typing import Dict, List, Optional, Tuple, Union

from clipped.compact.pydantic import Field

from polyaxon._schemas.base import BaseSchemaModel


class V1EnvVar(BaseSchemaModel):
    __root__: Union[Tuple[str, str], Dict[str, str]]

    def to_cmd(self):
        if isinstance(self.__root__, tuple):
            value = self.__root__
        else:
            value = self.__root__.items()
        return [f"{value[0]}={value[1]}"]


class V1Container(BaseSchemaModel):
    name: Optional[str]
    command: Optional[List[str]]
    args: Optional[List[str]]
    env: Optional[List[V1EnvVar]]
    working_dir: Optional[str] = Field(alias="workingDir")

    def get_cmd_args(self):
        cmd_args = ["run", "--rm"]
        for env in self.env:
            cmd_args += ["-e"] + env.to_cmd()
        if self.working_dir:
            cmd_args += ["-w", self.working_dir]
        if self.command:
            cmd_args += ["--entrypoint", self.command[0]]
        cmd_args += [self.image]
        if self.command:
            cmd_args += self.command[1:]
        if self.args:
            cmd_args += self.args
        return cmd_args
