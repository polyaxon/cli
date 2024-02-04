import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1StatusCondition, V1Statuses


class V1Agent(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    live_state: Optional[int]
    namespace: Optional[StrictStr]
    version_api: Optional[Dict[str, Any]]
    version: Optional[StrictStr]
    content: Optional[StrictStr]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    status: Optional[V1Statuses]
    status_conditions: Optional[List[V1StatusCondition]]
    is_replica: Optional[bool]
    is_ui_managed: Optional[bool]
    settings: Optional[Dict[str, Any]]
