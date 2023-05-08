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

from typing import List

from polyaxon.contexts import paths as ctx_paths


def get_artifacts_store_args(artifacts_path: str, clean: bool) -> str:
    get_or_create = 'if [ ! -d "{dir}" ]; then mkdir -m 0777 -p {dir}; fi;'.format(
        dir=artifacts_path
    )
    delete_dir = (
        'if [ -d {path} ] && [ "$(ls -A {path})" ]; '
        "then rm -R {path}/*; fi;".format(path=artifacts_path)
    )
    if clean:
        return "{} {}".format(get_or_create, delete_dir)
    return "{}".format(get_or_create)


def init_artifact_context_args(run_path: str) -> List[str]:
    return [
        'if [ ! -d "{dir}" ]; then mkdir -m 0777 -p {dir}; fi;'.format(
            dir=ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_path)
        ),
        'if [ ! -d "{dir}" ]; then mkdir -m 0777 -p {dir}; fi;'.format(
            dir=ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_path) + "/outputs"
        ),
    ]
