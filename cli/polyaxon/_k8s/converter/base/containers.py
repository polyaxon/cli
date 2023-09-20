from typing import Dict, List, Optional, Union

from clipped.utils.lists import to_list
from clipped.utils.sanitizers import sanitize_value

from polyaxon._containers.names import sanitize_container_name
from polyaxon._k8s import k8s_schemas
from polyaxon._runner.converter import BaseConverter
from polyaxon._runner.converter.common.containers import sanitize_container_command_args


class ContainerMixin(BaseConverter):
    @classmethod
    def _patch_container(
        cls,
        container: k8s_schemas.V1Container,
        name: Optional[str] = None,
        command: Optional[List[str]] = None,
        args: Optional[List[str]] = None,
        image: Optional[str] = None,
        image_pull_policy: Optional[str] = None,
        env: Optional[List[k8s_schemas.V1EnvVar]] = None,
        env_from: Optional[List[k8s_schemas.V1EnvFromSource]] = None,
        volume_mounts: Optional[List[k8s_schemas.V1VolumeMount]] = None,
        ports: Optional[List[k8s_schemas.V1ContainerPort]] = None,
        resources: Optional[k8s_schemas.V1ResourceRequirements] = None,
    ) -> k8s_schemas.V1Container:
        container.name = sanitize_container_name(name or container.name)
        container.env = to_list(container.env, check_none=True) + to_list(
            env, check_none=True
        )
        container.env_from = to_list(container.env_from, check_none=True) + to_list(
            env_from, check_none=True
        )
        container.volume_mounts = to_list(
            container.volume_mounts, check_none=True
        ) + to_list(volume_mounts, check_none=True)
        container.ports = to_list(container.ports, check_none=True) + to_list(
            ports, check_none=True
        )
        container.resources = container.resources or resources
        container._image_pull_policy = container.image_pull_policy or image_pull_policy
        container.image = container.image or image

        if not any([container.command, container.args]):
            container.command = command
            container.args = args

        return cls._sanitize_container(container)

    @staticmethod
    def _sanitize_container_env(
        env: List[k8s_schemas.V1EnvVar],
    ) -> Optional[List[k8s_schemas.V1EnvVar]]:
        def sanitize_env_dict(d: Dict):
            return {
                d_k: sanitize_value(d_v, handle_dict=False)
                if d_k in ["name", "value"]
                else sanitize_value(d_v, handle_dict=True)
                for d_k, d_v in d.items()
            }

        results = []
        for e in env or []:
            if isinstance(e, dict):
                e = sanitize_env_dict(e)
                results.append(e)
            elif isinstance(e, k8s_schemas.V1EnvVar):
                if e.value is not None:
                    e.value = sanitize_value(e.value, handle_dict=False)
                results.append(e)
        return results

    @staticmethod
    def _sanitize_resources(
        resources: Union[k8s_schemas.V1ResourceRequirements, Dict]
    ) -> Optional[k8s_schemas.V1ResourceRequirements]:
        def validate_resources(r_field: Dict) -> Dict:
            if not r_field:
                return r_field

            for k in r_field:
                r_field[k] = str(r_field[k])

            return r_field

        if not resources:
            return None

        if isinstance(resources, Dict):
            return k8s_schemas.V1ResourceRequirements(
                limits=validate_resources(resources.get("limits", None)),
                requests=validate_resources(resources.get("requests", None)),
            )
        else:
            return k8s_schemas.V1ResourceRequirements(
                limits=validate_resources(resources.limits),
                requests=validate_resources(resources.requests),
            )

    @classmethod
    def _sanitize_container(
        cls,
        container: k8s_schemas.V1Container,
    ) -> k8s_schemas.V1Container:
        container = sanitize_container_command_args(container)
        container.resources = cls._sanitize_resources(container.resources)
        container.env = cls._sanitize_container_env(container.env)
        return container
