from typing import Any, Dict, List, Optional

from clipped.utils.lists import to_list
from clipped.utils.sanitizers import sanitize_value

from polyaxon._containers.names import sanitize_container_name
from polyaxon._local_process import process_types
from polyaxon._runner.converter import BaseConverter
from polyaxon._runner.converter.common.containers import sanitize_container_command_args


class ContainerMixin(BaseConverter):
    @classmethod
    def _patch_container(
        cls,
        container: process_types.V1Container,
        name: Optional[str] = None,
        command: Optional[List[str]] = None,
        args: Optional[List[str]] = None,
        env: Optional[List[process_types.V1EnvVar]] = None,
        env_from: Optional[List[Any]] = None,
        **kwargs,
    ) -> process_types.V1Container:
        container.name = sanitize_container_name(name or container.name)
        container.env = to_list(container.env, check_none=True) + to_list(
            env, check_none=True
        )
        if not any([container.command, container.args]):
            container.command = command
            container.args = args

        return cls._sanitize_container(container)

    @staticmethod
    def _sanitize_container_env(
        env: List[process_types.V1EnvVar],
    ) -> List[process_types.V1EnvVar]:
        def sanitize_env_dict(d: Dict):
            return process_types.V1EnvVar(
                __root__={
                    d_k: sanitize_value(d_v, handle_dict=False)
                    for d_k, d_v in d.items()
                }
            )

        results = []
        for e in env or []:
            if isinstance(e, dict):
                e = sanitize_env_dict(e)
                results.append(e)
            elif isinstance(e, tuple):
                if e[1] is not None:
                    e = process_types.V1EnvVar(
                        __root__=(e[0], sanitize_value(e[1], handle_dict=False))
                    )
                results.append(e)
            elif isinstance(e, process_types.V1EnvVar):
                results.append(e)

        return results

    @classmethod
    def _sanitize_container(
        cls,
        container: process_types.V1Container,
    ) -> process_types.V1Container:
        container = sanitize_container_command_args(container)
        container.env = cls._sanitize_container_env(container.env)
        return container
