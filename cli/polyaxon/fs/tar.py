import os

from typing import List, Optional

from clipped.utils.paths import create_tarfile, get_files_in_path

from polyaxon import settings


def tar_dir(download_path: str) -> str:
    outputs_files = get_files_in_path(download_path)
    tar_base_name = os.path.basename(download_path)
    tar_name = "{}.tar.gz".format(tar_base_name)
    target_path = os.path.join(settings.CLIENT_CONFIG.archives_root or "", tar_name)
    create_tarfile(files=outputs_files, tar_path=target_path, relative_to=download_path)
    return target_path


def tar_files(
    download_name: str, outputs_files: List[str], relative_to: Optional[str] = None
) -> str:
    tar_name = "{}.tar.gz".format(download_name)
    target_path = os.path.join(settings.CLIENT_CONFIG.archives_root or "", tar_name)
    create_tarfile(files=outputs_files, tar_path=target_path, relative_to=relative_to)
    return target_path
