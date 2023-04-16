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

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from clipped.utils.dates import path_last_modified
from clipped.utils.json import orjson_dumps
from clipped.utils.paths import get_files_and_dirs_in_path

from polyaxon.contexts import paths as ctx_paths
from polyaxon.schemas.base import BaseSchemaModel


class PathData(BaseSchemaModel):
    __root__: Tuple[str, datetime, str]

    @property
    def base(self) -> str:
        return self.__root__[0]

    @property
    def ts(self) -> datetime:
        return self.__root__[1]

    @property
    def op(self) -> str:
        return self.__root__[2]


class FSWatcher(BaseSchemaModel):
    _IDENTIFIER = "fswatcher"

    _PUT = "put"
    _RM = "rm"
    _NOOP = ""

    dir_mapping: Optional[Dict[str, PathData]]
    file_mapping: Optional[Dict[str, PathData]]

    class Config(BaseSchemaModel.Config):
        validate_assignment = False

    @classmethod
    def _dump(cls, obj_dict: Dict) -> str:
        return orjson_dumps(obj_dict)

    @staticmethod
    def delete(path: str):
        if os.path.exists(path):
            os.remove(path)

    def write(self, filepath: str, mode: Optional[int] = None):
        filepath = filepath or ctx_paths.CONTEXT_MOUNT_FILE_WATCHER
        return super().write(filepath=filepath, mode=mode)

    def _sync_path(self, path: str, base_path: str, mapping: Dict) -> Dict:
        current_ts = path_last_modified(path)
        rel_path = os.path.relpath(path, base_path)
        data = mapping.get(rel_path)
        if data:
            if current_ts > data.ts:
                mapping[rel_path] = PathData.construct(base_path, current_ts, self._PUT)
            else:
                mapping[rel_path] = PathData.construct(base_path, data.ts, self._NOOP)
        else:
            mapping[rel_path] = PathData.construct(base_path, current_ts, self._PUT)
        return mapping

    def sync_file(self, path: str, base_path: str):
        self.file_mapping = self._sync_path(path, base_path, self.file_mapping)

    def sync_dir(self, path: str, base_path: str):
        self.dir_mapping = self._sync_path(path, base_path, self.dir_mapping)

    def init(self):
        self.dir_mapping = {
            p: PathData.construct(d.base, d.ts, self._RM)
            for p, d in self.dir_mapping.items()
        }
        self.file_mapping = {
            p: PathData.construct(d.base, d.ts, self._RM)
            for p, d in self.file_mapping.items()
        }

    def sync(self, path: str, exclude: Optional[List[str]] = None):
        files, dirs = get_files_and_dirs_in_path(
            path, exclude=exclude, collect_dirs=True
        )
        base_path, prefix_path = os.path.split(path)
        for file_path in files:
            self.sync_file(os.path.join(prefix_path, file_path), base_path=base_path)

        for dir_path in dirs:
            self.sync_dir(os.path.join(prefix_path, dir_path), base_path=base_path)

    def _get_mapping_by_op(self, mapping: Dict, op: str) -> Set:
        return {(p.base, k) for k, p in mapping.items() if p.op == op}

    def _clean_by_op(self, mapping: Dict, op: str) -> Dict:
        return {k: p for k, p in mapping.items() if p.op != op}

    def get_files_to_put(self) -> Set:
        return self._get_mapping_by_op(self.file_mapping, self._PUT)

    def get_files_to_rm(self) -> Set:
        results = self._get_mapping_by_op(self.file_mapping, self._RM)
        self.file_mapping = self._clean_by_op(self.file_mapping, self._RM)
        return results

    def get_dirs_to_put(self) -> Set:
        return self._get_mapping_by_op(self.dir_mapping, self._PUT)

    def get_dirs_to_rm(self) -> Set:
        results = self._get_mapping_by_op(self.dir_mapping, self._RM)
        self.file_mapping = self._clean_by_op(self.file_mapping, self._RM)
        return results
