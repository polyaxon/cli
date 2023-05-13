import datetime

from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.connections import V1ConnectionKind
from polyaxon.schemas.base import BaseSchemaModel


class V1ConnectionResponse(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    agent: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    live_state: Optional[int]
    kind: Optional[V1ConnectionKind]
