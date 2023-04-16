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

from clipped.types.gcs import GcsPath
from clipped.types.s3 import S3Path
from clipped.types.uri import Uri
from clipped.types.wasb import WasbPath

from polyaxon.schemas.types.artifacts import V1ArtifactsType
from polyaxon.schemas.types.connections import V1ConnectionType
from polyaxon.schemas.types.dockerfile import V1DockerfileType
from polyaxon.schemas.types.event import V1EventType
from polyaxon.schemas.types.file import V1FileType
from polyaxon.schemas.types.git import V1GitType
from polyaxon.schemas.types.k8s_resources import V1K8sResourceType
from polyaxon.schemas.types.tensorboard import V1TensorboardType

V1GcsType = GcsPath
V1S3Type = S3Path
V1UriType = Uri
V1WasbType = WasbPath
