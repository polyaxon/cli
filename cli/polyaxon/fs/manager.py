#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
