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

# Container names are Kubernetes DNS labels, capped at 63 characters.
MAX_CONTAINER_NAME_LENGTH = 63


def _trim(value: str, max_length: int) -> str:
    """Cut a name component down to `max_length` characters.

    A DNS label must start and end with an alphanumeric character, so any
    dashes exposed by the cut are stripped as well.
    """
    if max_length <= 0:
        return ""
    return value[:max_length].strip("-")


def generate_container_name(
    prefix: str, suffix: Optional[str] = None, unique: bool = True
) -> str:
    import uuid

    prefix = prefix or "container"
    unique_value = uuid.uuid4().hex[:10]
    if suffix:
        suffix = suffix.replace("_", "-")
        if unique:
            # Reserve room for the prefix, the two joining dashes and the
            # unique value so that the generated name always stays within the
            # Kubernetes limit, and trim the caller-supplied part only.
            budget = MAX_CONTAINER_NAME_LENGTH - len(prefix) - len(unique_value) - 2
            suffix = "{}-{}".format(_trim(suffix, budget), unique_value)
        else:
            suffix = _trim(suffix, MAX_CONTAINER_NAME_LENGTH - len(prefix) - 1)
    else:
        suffix = unique_value
    return sanitize_container_name("{}-{}".format(prefix, suffix))


def sanitize_container_name(name: str) -> str:
    name = name.replace("_", "-").lower()
    return _trim(name, MAX_CONTAINER_NAME_LENGTH)
