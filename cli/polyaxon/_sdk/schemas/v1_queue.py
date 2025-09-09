import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Queue(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    agent: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    user: Optional[StrictStr] = None
    priority: Optional[int] = None
    concurrency: Optional[int] = None
    resource: Optional[StrictStr] = None
    quota: Optional[StrictStr] = None
    stats: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
