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
