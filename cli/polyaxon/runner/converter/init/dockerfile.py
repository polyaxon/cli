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

from typing import List, Optional

from clipped.utils.lists import to_list

from polyaxon.auxiliaries import V1PolyaxonInitContainer
from polyaxon.containers.names import (
    INIT_DOCKERFILE_CONTAINER_PREFIX,
    generate_container_name,
)
from polyaxon.contexts import paths as ctx_paths
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.containers import patch_container
from polyaxon.k8s.converter.common.env_vars import get_run_instance_env_var
from polyaxon.k8s.converter.common.mounts import (
    get_auth_context_mount,
    get_connections_context_mount,
)
from polyaxon.k8s.converter.common.volumes import get_volume_name
from polyaxon.polyflow import V1Plugins
from polyaxon.runner.converter.common import constants
from polyaxon.schemas.types import V1DockerfileType

INIT_DOCKERFILE_COMMAND = ["polyaxon", "docker", "generate"]


def get_dockerfile_init_container(
    dockerfile_args: V1DockerfileType,
    run_path: str,
    mount_path: Optional[str] = None,
) -> List[str]:
    return [
        "--build-context={}".format(dockerfile_args.to_json()),
        "--destination={}".format(mount_path),
        "--copy-path={}".format(
            ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format(run_path)
        ),
        "--track",
    ]
