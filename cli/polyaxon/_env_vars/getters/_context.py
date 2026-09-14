import os
from typing import NamedTuple, Optional


class _ContextSource(NamedTuple):
    kind: str = "explicit"
    path: Optional[str] = None

    def describe(self) -> str:
        return f"{self.kind} · {self.path}" if self.path else self.kind


def _get_cache_source(manager) -> _ContextSource:
    path = os.path.abspath(manager.get_config_filepath(create=False))
    is_local = not manager.is_global() and path == os.path.abspath(
        manager.get_local_config_path()
    )
    return _ContextSource("local cache" if is_local else "global cache", path)
