import os

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from clipped.utils.dates import path_last_modified
from clipped.utils.paths import get_files_and_dirs_in_path

from polyaxon._contexts import paths as ctx_paths
from polyaxon._schemas.base import BaseSchemaModel


class PathData(BaseSchemaModel):
    __root__: Tuple[str, datetime, str]

    class Config(BaseSchemaModel.Config):
        validate_assignment = False

    @property
    def base(self) -> str:
        return self.__root__[0]

    @property
    def ts(self) -> datetime:
        if isinstance(self.__root__[1], str):
            self.__root__ = (
                self.__root__[0],
                datetime.fromisoformat(self.__root__[1]),
                self.__root__[1],
            )
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

    @property
    def dirs_mp(self) -> Dict[str, PathData]:
        return self.dir_mapping or {}

    @property
    def files_mp(self) -> Dict[str, PathData]:
        return self.file_mapping or {}

    class Config(BaseSchemaModel.Config):
        validate_assignment = False

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
                mapping[rel_path] = PathData.construct(
                    __root__=(base_path, current_ts, self._PUT)
                )
            else:
                mapping[rel_path] = PathData.construct(
                    __root__=(base_path, data.ts, self._NOOP)
                )
        else:
            mapping[rel_path] = PathData.construct(
                __root__=(base_path, current_ts, self._PUT)
            )
        return mapping

    def sync_file(self, path: str, base_path: str):
        self.file_mapping = self._sync_path(path, base_path, self.files_mp)

    def sync_dir(self, path: str, base_path: str):
        self.dir_mapping = self._sync_path(path, base_path, self.dirs_mp)

    def init(self):
        self.dir_mapping = {
            p: PathData.construct(__root__=(d.base, d.ts, self._RM))
            for p, d in self.dirs_mp.items()
        }
        self.file_mapping = {
            p: PathData.construct(__root__=(d.base, d.ts, self._RM))
            for p, d in self.files_mp.items()
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
        return self._get_mapping_by_op(self.files_mp, self._PUT)

    def get_files_to_rm(self) -> Set:
        results = self._get_mapping_by_op(self.files_mp, self._RM)
        self.file_mapping = self._clean_by_op(self.files_mp, self._RM)
        return results

    def get_dirs_to_put(self) -> Set:
        return self._get_mapping_by_op(self.dirs_mp, self._PUT)

    def get_dirs_to_rm(self) -> Set:
        results = self._get_mapping_by_op(self.dirs_mp, self._RM)
        self.dir_mapping = self._clean_by_op(self.dirs_mp, self._RM)
        return results
