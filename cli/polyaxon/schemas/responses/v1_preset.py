import datetime

from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1Preset(BaseResponseModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    frozen: Optional[bool]
    live_state: Optional[int]
    content: Optional[StrictStr]
