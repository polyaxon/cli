from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon._schemas.types.base import BaseTypeConfig


class V1EventType(BaseTypeConfig):
    _IDENTIFIER = "event"

    name: Optional[StrictStr]
    kind: Optional[StrictStr]
