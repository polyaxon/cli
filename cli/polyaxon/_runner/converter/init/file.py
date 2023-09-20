from typing import List, Optional

from polyaxon._contexts import paths as ctx_paths
from polyaxon._schemas.types import V1FileType

FILE_INIT_COMMAND = ["polyaxon", "initializer", "file"]


def get_file_init_args(
    file_args: V1FileType,
    run_path: str,
    mount_path: Optional[str] = None,
) -> List[str]:
    return [
        "--file-context={}".format(file_args.to_json()),
        "--filepath={}".format(mount_path),
        "--copy-path={}".format(
            ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format(run_path)
        ),
        "--track",
    ]
