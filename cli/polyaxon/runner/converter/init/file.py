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

from typing import List, Optional

from polyaxon.contexts import paths as ctx_paths
from polyaxon.schemas.types import V1FileType

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
