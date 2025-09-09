import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_project_settings import V1ProjectSettings


class V1Project(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    owner: Optional[StrictStr] = None
    user: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    is_public: Optional[bool] = None
    bookmarked: Optional[bool] = None
    readme: Optional[StrictStr] = None
    excluded_features: Optional[List[StrictStr]] = None
    excluded_runtimes: Optional[List[StrictStr]] = None
    archived_deletion_interval: Optional[int] = None
    settings: Optional[V1ProjectSettings] = None
    role: Optional[StrictStr] = None
    contributors: Optional[List[Dict[str, Any]]] = None
    live_state: Optional[int] = None
