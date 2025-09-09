import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1StatusCondition, V1Statuses


class V1Agent(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    live_state: Optional[int] = None
    user: Optional[StrictStr] = None
    namespace: Optional[StrictStr] = None
    version_api: Optional[Dict[str, Any]] = None
    version: Optional[StrictStr] = None
    content: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    status: Optional[V1Statuses] = None
    status_conditions: Optional[List[V1StatusCondition]] = None
    is_replica: Optional[bool] = None
    is_ui_managed: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
