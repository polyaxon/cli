import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_project_settings import V1ProjectSettings


class V1Project(BaseAllowSchemaModel):
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
    archived_deletion_interval: Optional[int]
    settings: Optional[V1ProjectSettings]
    role: Optional[StrictStr]
    contributors: Optional[Dict[str, Any]]
    live_state: Optional[int]
