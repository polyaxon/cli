import jinja2
import os

from typing import List, Tuple, Union

from clipped.utils.lists import to_list

from polyaxon._docker.builder.dockerfile import POLYAXON_DOCKER_TEMPLATE
from polyaxon._schemas.types import V1DockerfileType


class DockerFileGenerator:
    def __init__(self, build_context: V1DockerfileType, destination: str = "."):
        self.build_context = build_context
        self.dockerfile_path = os.path.join(destination, build_context.get_filename())

    def clean(self):
        # Clean dockerfile
        if not os.path.exists(self.dockerfile_path):
            return
        os.remove(self.dockerfile_path)

    def create(self, save: bool = True) -> str:
        # Create DockerFile
        rendered_dockerfile = self.render()
        if save:
            with open(self.dockerfile_path, "w") as dockerfile:
                dockerfile.write(rendered_dockerfile)
        return rendered_dockerfile

    @staticmethod
    def get_copy(
        copy: Union[List[str], List[Tuple[str, str]]], workdir: str
    ) -> List[List[str]]:
        copy = to_list(copy, check_none=True)

        def handle_copy(c: Union[str, List]):
            if isinstance(c, str):
                return [c, workdir]
            return c

        return [handle_copy(c) for c in copy]

    def render(self):
        docker_template = jinja2.Template(POLYAXON_DOCKER_TEMPLATE)
        return docker_template.render(
            image=self.build_context.image,
            copy=self.get_copy(self.build_context.copy_, self.build_context.workdir),
            post_run_copy=self.get_copy(
                self.build_context.post_run_copy, self.build_context.workdir
            ),
            run=to_list(self.build_context.run, check_none=True),
            env=to_list(self.build_context.env, check_none=True, check_dict=True),
            workdir=self.build_context.workdir,
            path=to_list(self.build_context.path, check_none=True),
            workdir_path=self.build_context.workdir_path,
            lang_env=self.build_context.lang_env,
            uid=self.build_context.uid,
            gid=self.build_context.gid,
            username=self.build_context.username or "polyaxon",
            shell=self.build_context.shell,
        )
