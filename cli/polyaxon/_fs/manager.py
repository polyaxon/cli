from typing import List, Union

from clipped.utils.lists import to_list
from clipped.utils.paths import check_or_create_path
from fsspec import AbstractFileSystem

from polyaxon.logger import logger


def download_file_or_dir(
    fs: AbstractFileSystem,
    path_from: str,
    path_to: str,
    is_file: bool,
    check_path: bool,
):
    if check_path:
        is_file = fs.isfile(path_from)
    check_or_create_path(path_to, is_dir=not is_file)
    if not is_file:
        path_to = path_to.rstrip("/") + "/"
        path_from = path_from.rstrip("/") + "/"
    fs.download(rpath=path_from, lpath=path_to, recursive=not is_file)


def delete_file_or_dir(
    fs: AbstractFileSystem,
    subpath: Union[str, List[str]],
    is_file: bool = False,
):
    subpath = to_list(subpath, check_none=True)
    for sp in subpath:
        try:
            fs.delete(path=sp, recursive=not is_file)
        except Exception as e:
            logger.info("Could not delete path %s\nError: %s", sp, e)
