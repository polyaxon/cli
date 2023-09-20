import os

from typing import List, Optional

from polyaxon._contexts import paths as ctx_paths
from polyaxon._fs.async_manager import ensure_async_execution
from polyaxon._fs.types import FSSystem
from polyaxon._fs.watcher import FSWatcher
from polyaxon.logger import logger

from fsspec.asyn import _run_coros_in_chunks  # noqa


async def sync_fs(
    fs: FSSystem,
    fw: FSWatcher,
    store_base_path: str,
):
    def get_store_path(subpath: str):
        return os.path.join(store_base_path, subpath)

    rm_files = fw.get_files_to_rm()
    logger.debug("rm_files {}".format(rm_files))

    await _run_coros_in_chunks(
        [
            ensure_async_execution(
                fs=fs,
                fct="rm_file",
                is_async=fs.async_impl,
                path=get_store_path(subpath),
                recursive=False,
            )
            for (_, subpath) in rm_files
        ],
        return_exceptions=True,
        nofiles=True,
    )
    rm_dirs = fw.get_dirs_to_rm()
    logger.debug("rm_dirs {}".format(rm_dirs))
    await _run_coros_in_chunks(
        [
            ensure_async_execution(
                fs=fs,
                fct="rm",
                is_async=fs.async_impl,
                path=get_store_path(subpath),
                recursive=True,
            )
            for (_, subpath) in rm_dirs
        ],
        return_exceptions=True,
        nofiles=True,
    )
    put_files = fw.get_files_to_put()
    logger.debug("put_files {}".format(put_files))
    await _run_coros_in_chunks(
        [
            ensure_async_execution(
                fs=fs,
                fct="put",
                is_async=fs.async_impl,
                lpath=os.path.join(r_base_path, subpath),
                rpath=get_store_path(subpath),
                recursive=False,
            )
            for (r_base_path, subpath) in put_files
        ],
        return_exceptions=True,
        nofiles=True,
    )


async def sync_artifacts(
    fs: FSSystem,
    fw: FSWatcher,
    store_path: str,
    run_uuid: str,
    exclude: Optional[List[str]] = None,
):
    fw.init()
    path_from = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_uuid)
    fw.sync(path_from, exclude=exclude)

    # Check if this run has triggered some related run paths
    if os.path.exists(ctx_paths.CONTEXT_MOUNT_ARTIFACTS_RELATED):
        for sub_path in os.listdir(ctx_paths.CONTEXT_MOUNT_ARTIFACTS_RELATED):
            # check if there's a path to sync
            path_from = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_RELATED_FORMAT.format(
                sub_path
            )
            fw.sync(path_from, exclude=exclude)

    await sync_fs(
        fs=fs,
        fw=fw,
        store_base_path=store_path,
    )
