from typing import TYPE_CHECKING, Union

from clipped.formatting import Printer
from clipped.utils.enums import get_enum_value

from polyaxon._contexts import paths as ctx_paths
from polyaxon._fs.watcher import FSWatcher
from polyaxon.logger import logger

if TYPE_CHECKING:
    from polyaxon._connections import V1ConnectionKind


def sync_file_watcher(path: str):
    try:
        fw = FSWatcher()
        fw.sync(path)
        fw.write(ctx_paths.CONTEXT_MOUNT_FILE_WATCHER)
    except Exception as e:  # File watcher should not prevent job from starting
        logger.warning(
            "File watcher failed syncing path: {}.\nError: {}".format(path, e)
        )


def download_artifact(
    connection_name: str,
    connection_kind: Union[str, "V1ConnectionKind"],
    path_from: str,
    path_to: str,
    is_file: bool,
    raise_errors: bool,
    sync_fw: bool,
    check_path: bool,
):
    from polyaxon._fs.fs import get_fs_from_name
    from polyaxon._fs.manager import download_file_or_dir

    fs = get_fs_from_name(connection_name=connection_name)
    try:
        download_file_or_dir(
            fs=fs,
            path_from=path_from,
            path_to=path_to,
            is_file=is_file,
            check_path=check_path,
        )
        if sync_fw:
            sync_file_watcher(path_to)
        Printer.success(
            "{} path is initialized, path: `{}`".format(
                get_enum_value(connection_kind), path_to
            )
        )
    except Exception as e:
        if raise_errors:
            raise e
        else:
            logger.debug(
                "Initialization failed, the error was ignored. Error details %s", e
            )
