import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.uuids import UUIDStr

from polyaxon.schemas.base import BaseResponseModel


class V1Token(BaseResponseModel):
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
