import datetime

from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_project_settings import V1ProjectSettings


class V1Project(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    owner: Optional[StrictStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    is_public: Optional[bool]
    bookmarked: Optional[bool]
    readme: Optional[StrictStr]
    excluded_features: Optional[List[StrictStr]]
    excluded_runtimes: Optional[List[StrictStr]]
    settings: Optional[V1ProjectSettings]
    role: Optional[StrictStr]
    live_state: Optional[int]
