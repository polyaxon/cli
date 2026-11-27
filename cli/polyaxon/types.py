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
