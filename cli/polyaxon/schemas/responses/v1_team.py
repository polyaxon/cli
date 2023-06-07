import datetime

from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_team_settings import V1TeamSettings


class V1Team(BaseResponseModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    projects: Optional[List[StrictStr]]
    component_hubs: Optional[List[StrictStr]]
    model_registries: Optional[List[StrictStr]]
    settings: Optional[V1TeamSettings]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
