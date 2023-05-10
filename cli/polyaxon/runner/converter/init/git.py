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
import os

from typing import List, Optional

from clipped.utils.json import orjson_dumps
from clipped.utils.lists import to_list

from polyaxon.exceptions import PolyaxonConverterError

REPO_INIT_COMMAND = ["polyaxon", "initializer", "git"]


def get_repo_context_args(
    name: str,
    url: str,
    revision: str,
    mount_path: str,
    connection: Optional[str] = None,
    flags: Optional[List[str]] = None,
) -> List[str]:
    if not name:
        raise PolyaxonConverterError(
            "A repo name is required to create a repo context."
        )
    if not url:
        raise PolyaxonConverterError("A repo url is required to create a repo context.")

    args = [
        "--repo-path={}".format(os.path.join(mount_path, name)),
        "--url={}".format(url),
    ]

    if revision:
        args.append("--revision={}".format(revision))

    if connection:
        args.append("--connection={}".format(connection))

    flags = to_list(flags, check_none=True)
    if flags:
        args.append("--flags={}".format(orjson_dumps(flags)))
    return args
