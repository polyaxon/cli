#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections.abc import Mapping
from typing import Dict, List, Optional

from clipped.utils.lists import to_list
from clipped.utils.sanitizers import sanitize_value

from polyaxon.containers.names import sanitize_container_name
from polyaxon.docker import docker_types
from polyaxon.k8s import k8s_schemas
from polyaxon.runner.converter.common.containers import sanitize_container_command_args


def patch_container(
    container: docker_types.V1Container,
    name: Optional[str] = None,
    command: Optional[List[str]] = None,
    args: Optional[List[str]] = None,
    image: Optional[str] = None,
    image_pull_policy: Optional[str] = None,
    env: Optional[List[docker_types.V1EnvVar]] = None,
    env_from: Optional[List[docker_types.V1EnvFromSource]] = None,
    volume_mounts: Optional[List[docker_types.V1VolumeMount]] = None,
    ports: Optional[List[docker_types.V1ContainerPort]] = None,
    resources: Optional[docker_types.V1ResourceRequirements] = None,
) -> docker_types.V1Container:
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

    return sanitize_container(container)


def sanitize_container_env(
    container: k8s_schemas.V1Container,
) -> k8s_schemas.V1Container:
    def sanitize_env_dict(d: Dict):
        return {
            d_k: sanitize_value(d_v, handle_dict=False)
            if d_k in ["name", "value"]
            else sanitize_value(d_v, handle_dict=True)
            for d_k, d_v in d.items()
        }

    if container.env:
        env = []
        for e in container.env:
            if isinstance(e, Mapping):
                e = sanitize_env_dict(e)
                env.append(e)
            elif isinstance(e, k8s_schemas.V1EnvVar):
                if e.value is not None:
                    e.value = sanitize_value(e.value, handle_dict=False)
                env.append(e)

        container.env = env
    return container


def sanitize_container(
    container: k8s_schemas.V1Container,
) -> k8s_schemas.V1Container:
    container = sanitize_container_command_args(container)
    container.resources = sanitize_resources(container.resources)
    return sanitize_container_env(container)
