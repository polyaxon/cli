from typing import Any, Dict

from clipped.utils.enums import get_enum_value

from polyaxon.exceptions import PolyaxonAgentError


class BaseExecutor:
    _MIXIN_MAPPING: Dict[str, Any]

    def __init__(self):
        self._manager = None

    @classmethod
    def _get_mixin_for_kind(cls, kind: str) -> Any:
        m = cls._MIXIN_MAPPING.get(kind)
        if not m:
            raise PolyaxonAgentError(
                "Agent received unrecognized kind {}".format(get_enum_value(kind))
            )
        return m

    @property
    def manager(self):
        if not self._manager:
            self._manager = self._get_manager()
        return self._manager

    def _get_manager(self):
        raise NotImplementedError

    def refresh(self):
        self._manager = None
        return self.manager

    def get(self, run_uuid: str, run_kind: str):
        raise NotImplementedError

    def create(self, run_uuid: str, run_kind: str, resource: Dict):
        raise NotImplementedError

    def apply(self, run_uuid: str, run_kind: str, resource: Dict):
        raise NotImplementedError

    def stop(self, run_uuid: str, run_kind: str):
        raise NotImplementedError

    def clean(self, run_uuid: str, run_kind: str):
        raise NotImplementedError
