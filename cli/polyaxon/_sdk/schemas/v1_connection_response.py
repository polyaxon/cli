import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr
from vents.providers.kinds import ProviderKind


class V1ConnectionResponse(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    user: Optional[StrictStr] = None
    agent: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    live_state: Optional[int] = None
    kind: Optional[ProviderKind] = None
