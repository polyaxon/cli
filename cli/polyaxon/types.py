from clipped.types import FORWARDING as CLIPPED_FORWARDING
from clipped.types import MAPPING as CLIPPED_MAPPING
from clipped.types import *

from polyaxon._schemas.types import (
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
    "FileType": V1FileType,
    "DockerfileType": V1DockerfileType,
    "TensorboardType": V1TensorboardType,
    "GitType": V1GitType,
    "ageStr": ImageStr,
    "EventType": V1EventType,
    "ArtifactsType": V1ArtifactsType,
    "V1FileType": V1FileType,
    "V1DockerfileType": V1DockerfileType,
    "V1TensorboardType": V1TensorboardType,
    "V1GitType": V1GitType,
    "ImageStr": ImageStr,
    "V1EventType": V1EventType,
    "V1ArtifactsType": V1ArtifactsType,
}
