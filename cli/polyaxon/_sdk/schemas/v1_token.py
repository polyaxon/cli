import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Token(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    key: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    scopes: Optional[List[StrictStr]] = None
    services: Optional[List[StrictStr]] = None
    started_at: Optional[datetime.datetime] = None
    expires_at: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    expiration: Optional[int] = None
