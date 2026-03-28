import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_entity_level import V1EntityLevel
from polyaxon._sdk.schemas.v1_search_spec import V1SearchSpec


class V1Search(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    user: Optional[StrictStr] = None
    live_state: Optional[int] = None
    spec: Optional[V1SearchSpec] = None
    level: Optional[V1EntityLevel] = None
    project: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
