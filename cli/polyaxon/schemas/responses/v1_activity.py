import datetime

from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Activity(BaseAllowSchemaModel):
    actor: Optional[StrictStr]
    owner: Optional[StrictStr]
    created_at: Optional[datetime.datetime]
    event_action: Optional[StrictStr]
    event_subject: Optional[StrictStr]
    object_name: Optional[StrictStr]
    object_uuid: Optional[UUIDStr]
    object_parent: Optional[StrictStr]
