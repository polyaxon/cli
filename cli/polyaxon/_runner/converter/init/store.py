import os

from typing import List, Tuple, Union

from clipped.utils.enums import get_enum_value
from clipped.utils.lists import to_list

from polyaxon._connections import V1Connection
from polyaxon._schemas.types import V1ArtifactsType


def get_or_create_args(path):
    return 'if [ ! -d "{path}" ]; then mkdir -m 0777 -p {path}; fi;'.format(path=path)


def cp_mount_args(path_from, path_to, is_file: bool, sync_fw: bool) -> str:
    sync_fw_flag = (
        "polyaxon initializer fswatch --path={};".format(path_to) if sync_fw else ""
    )
    if is_file:
        return "if [ -f {path_from} ]; then cp {path_from} {path_to}; {sync_fw_flag} fi;".format(
            path_from=path_from,
            path_to=path_to,
            sync_fw_flag=sync_fw_flag,
        )
    return (
        'if [ -d {path_from} ] && [ "$(ls -A {path_from})" ]; '
        "then cp -R {path_from}/* {path_to}; {sync_fw_flag} fi;".format(
            path_from=path_from,
            path_to=path_to,
            sync_fw_flag=sync_fw_flag,
        )
    )


def cp_store_args(
    connection: str,
    backend: str,
    path_from: str,
    path_to: str,
    is_file: bool,
    check_path: bool,
    sync_fw: bool,
) -> str:
    args = []
    if is_file:
        args.append("--is-file")
    if sync_fw:
        args.append("--sync-fw")
    if check_path:
        args.append("--check-path")
    return "polyaxon initializer path --connection-name={} --connection-kind={} --path-from={} --path-to={} {};".format(
        connection, get_enum_value(backend), path_from, path_to, " ".join(args)
    )


def get_volume_args(
    store: V1Connection,
    mount_path: str,
    artifacts: V1ArtifactsType,
    paths: Union[List[str], List[Tuple[str, str]]],
    sync_fw: bool = False,
) -> str:
    files = []
    dirs = []
    paths = to_list(paths, check_none=True)
    if artifacts:
        files = artifacts.files or files
        dirs = artifacts.dirs or dirs
    # Default behavior is to pull all bucket
    if not files and not dirs and not paths:
        dirs = [""]
    args = []
    base_path_from = store.store_path

    def _copy():
        if isinstance(p, (list, tuple)):
            path_from = os.path.join(base_path_from, p[0])
            path_to = os.path.join(mount_path, p[1])
            _p = p[1]
        else:
            path_from = os.path.join(base_path_from, p)
            path_to = os.path.join(mount_path, p)
            _p = p

        # Create folders
        if is_file or check_path:
            # If we are initializing a file we need to create the base folder
            _p = os.path.split(_p)[0]
        base_path_to = os.path.join(mount_path, _p)
        # We need to check that the path exists first
        args.append(get_or_create_args(path=base_path_to))

        # copy to context
        if store.is_wasb:
            args.append(
                cp_store_args(
                    backend="wasb",
                    connection=store.name,
                    path_from=path_from,
                    path_to=path_to,
                    is_file=is_file,
                    sync_fw=sync_fw,
                    check_path=check_path,
                )
            )
        elif store.is_s3:
            args.append(
                cp_store_args(
                    backend="s3",
                    connection=store.name,
                    path_from=path_from,
                    path_to=path_to,
                    is_file=is_file,
                    sync_fw=sync_fw,
                    check_path=check_path,
                )
            )
        elif store.is_gcs:
            args.append(
                cp_store_args(
                    backend="gcs",
                    connection=store.name,
                    path_from=path_from,
                    path_to=path_to,
                    is_file=is_file,
                    sync_fw=sync_fw,
                    check_path=check_path,
                )
            )
        else:
            if check_path:
                args.append(
                    cp_store_args(
                        backend=store.kind,
                        connection=store.name,
                        path_from=path_from,
                        path_to=path_to,
                        is_file=is_file,
                        sync_fw=sync_fw,
                        check_path=check_path,
                    )
                )
            else:
                args.append(
                    cp_mount_args(
                        path_from=path_from,
                        path_to=path_to,
                        is_file=is_file,
                        sync_fw=sync_fw,
                    )
                )

    check_path = False
    is_file = True
    for p in files:
        _copy()

    is_file = False
    for p in dirs:
        # We need to check that the path exists first
        _copy()

    check_path = True
    for p in paths:
        _copy()

    return " ".join(args)
