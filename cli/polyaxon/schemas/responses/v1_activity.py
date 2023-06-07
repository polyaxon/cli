import datetime

from typing import Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1Activity(BaseResponseModel):
    actor: Optional[StrictStr]
    owner: Optional[StrictStr]
    created_at: Optional[datetime.datetime]
    event_action: Optional[StrictStr]
    event_subject: Optional[StrictStr]
    object_name: Optional[StrictStr]
    object_uuid: Optional[UUIDStr]
    object_parent: Optional[StrictStr]
