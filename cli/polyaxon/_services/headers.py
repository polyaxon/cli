from typing import Tuple

from clipped.utils.enums import PEnum, get_enum_value


class PolyaxonServiceHeaders(str, PEnum):
    CLI_VERSION = "X_POLYAXON_CLI_VERSION"
    CLIENT_VERSION = "X_POLYAXON_CLIENT_VERSION"
    INTERNAL = "X_POLYAXON_INTERNAL"
    SERVICE = "X_POLYAXON_SERVICE"

    @staticmethod
    def get_header(header) -> str:
        return get_enum_value(header).replace("_", "-")

    @classmethod
    def get_headers(cls) -> Tuple[str]:
        return tuple(cls.to_set() | {cls.get_header(h) for h in cls.to_set()})
