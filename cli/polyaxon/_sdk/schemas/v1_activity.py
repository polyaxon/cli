import datetime

from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Activity(BaseAllowSchemaModel):
    actor: Optional[StrictStr] = None
    owner: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    event_action: Optional[StrictStr] = None
    event_subject: Optional[StrictStr] = None
    object_name: Optional[StrictStr] = None
    object_uuid: Optional[UUIDStr] = None
    object_parent: Optional[StrictStr] = None
