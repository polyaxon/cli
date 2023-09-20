import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Token(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    key: Optional[StrictStr]
    name: Optional[StrictStr]
    scopes: Optional[List[StrictStr]]
    services: Optional[List[StrictStr]]
    started_at: Optional[datetime.datetime]
    expires_at: Optional[datetime.datetime]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    expiration: Optional[int]
