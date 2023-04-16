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

from clipped.types import FORWARDING as CLIPPED_FORWARDING
from clipped.types import MAPPING as CLIPPED_MAPPING
from clipped.types import *

from polyaxon.schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1EventType,
    V1FileType,
    V1GcsType,
    V1GitType,
    V1S3Type,
    V1TensorboardType,
    V1UriType,
    V1WasbType,
)

EVENT = "event"
DOCKERFILE = "dockerfile"
FILE = "file"
TENSORBOARD = "tensorboard"
GIT = "git"
ARTIFACTS = "artifacts"

LINEAGE_VALUES = {
    GCS,
    S3,
    WASB,
    DOCKERFILE,
    GIT,
    IMAGE,
    EVENT,
    ARTIFACTS,
    PATH,
    METRIC,
    METADATA,
}

MAPPING = {
    **CLIPPED_MAPPING,
    FILE: V1FileType,
    TENSORBOARD: V1TensorboardType,
    DOCKERFILE: V1DockerfileType,
    GIT: V1GitType,
    IMAGE: ImageStr,
    EVENT: V1EventType,
    ARTIFACTS: V1ArtifactsType,
}

FORWARDING = {
    **CLIPPED_FORWARDING,
    "V1FileType": V1FileType,
    "V1DockerfileType": V1DockerfileType,
    "V1TensorboardType": V1TensorboardType,
    "V1GitType": V1GitType,
    "ImageStr": ImageStr,
    "V1EventType": V1EventType,
    "V1ArtifactsType": V1ArtifactsType,
}
