import hashlib
import re
from typing import Optional


MAIN_JOB_CONTAINER = "polyaxon-main"
SIDECAR_CONTAINER = "polyaxon-sidecar"
TFJOBS_CONTAINER = "tensorflow"
PYTORCHJOBS_CONTAINER = "pytorch"
MAIN_CONTAINER_NAMES = [
    MAIN_JOB_CONTAINER,
    TFJOBS_CONTAINER,
    PYTORCHJOBS_CONTAINER,
]
INIT_AUTH_CONTAINER = "polyaxon-init-auth"
INIT_TOOLS_CONTAINER = "polyaxon-init-tools"
INIT_DOCKERFILE_CONTAINER_PREFIX = "polyaxon-init-dockerfile"
INIT_FILE_CONTAINER_PREFIX = "polyaxon-init-file"
INIT_TENSORBOARD_CONTAINER_PREFIX = "polyaxon-init-tb"
INIT_GIT_CONTAINER_PREFIX = "polyaxon-init-git"
INIT_CUSTOM_CONTAINER_PREFIX = "polyaxon-init-custom"
INIT_ARTIFACTS_CONTAINER_PREFIX = "polyaxon-init-artifacts"
POLYAXON_INIT_PREFIX = "polyaxon-init"
INIT_PREFIX = "init"
SIDECAR_PREFIX = "sidecar"


def generate_container_name(
    prefix: str, suffix: Optional[str] = None, unique: bool = True
) -> str:
    import uuid

    name = prefix or "container"
    if suffix:
        name = "{}-{}".format(name, suffix)

    unique_value = uuid.uuid4().hex[:10] if unique or not suffix else None
    candidate = "{}-{}".format(name, unique_value) if unique_value else name
    if len(candidate) <= 63 and re.fullmatch(
        r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", candidate
    ):
        return candidate

    name = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "container"
    if unique_value is None:
        if len(name) <= 63:
            return name
        unique_value = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:10]

    return "{}-{}".format(name[:52].rstrip("-"), unique_value)


def sanitize_container_name(name: str) -> str:
    name = name.replace("_", "-")
    return name.lower()
