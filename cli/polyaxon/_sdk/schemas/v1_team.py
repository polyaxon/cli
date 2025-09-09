import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_team_settings import V1TeamSettings


class V1Team(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    owner: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    user: Optional[StrictStr] = None
    projects: Optional[List[StrictStr]] = None
    component_hubs: Optional[List[StrictStr]] = None
    model_registries: Optional[List[StrictStr]] = None
    settings: Optional[V1TeamSettings] = None
    policy: Optional[StrictStr] = None
    role: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
