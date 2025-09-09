import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_search_spec import V1SearchSpec
from traceml.events.schemas import SearchView


class V1Search(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    user: Optional[StrictStr] = None
    live_state: Optional[int] = None
    view: Optional[SearchView] = None
    spec: Optional[V1SearchSpec] = None
    org_level: Optional[bool] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
