import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Queue(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    agent: Optional[StrictStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    priority: Optional[int]
    concurrency: Optional[int]
    resource: Optional[StrictStr]
    quota: Optional[StrictStr]
    stats: Optional[Dict[str, Any]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
