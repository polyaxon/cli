import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_team_settings import V1TeamSettings


class V1Team(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    owner: Optional[StrictStr]
    name: Optional[StrictStr]
    projects: Optional[List[StrictStr]]
    component_hubs: Optional[List[StrictStr]]
    model_registries: Optional[List[StrictStr]]
    settings: Optional[V1TeamSettings]
    role: Optional[StrictStr]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
