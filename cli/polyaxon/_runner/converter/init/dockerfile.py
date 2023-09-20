from typing import List, Optional

from polyaxon._contexts import paths as ctx_paths
from polyaxon._schemas.types import V1DockerfileType

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
