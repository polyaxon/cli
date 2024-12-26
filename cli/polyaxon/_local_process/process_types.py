from typing import Dict, List, Optional, Tuple, Union

from clipped.compact.pydantic import PYDANTIC_VERSION, Field

from polyaxon._schemas.base import BaseSchemaModel, RootModel


class V1EnvVar(RootModel):
    if PYDANTIC_VERSION.startswith("2."):
        root: Union[Tuple[str, str], Dict[str, str]]
    else:
        __root__: Union[Tuple[str, str], Dict[str, str]]

    def to_cmd(self):
        if isinstance(self._root, tuple):
            value = self._root
        else:
            value = self._root.items()
        return [f"{value[0]}={value[1]}"]


class V1Container(BaseSchemaModel):
    name: Optional[str] = None
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    env: Optional[List[V1EnvVar]] = None
    working_dir: Optional[str] = Field(alias="workingDir", default=None)

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
