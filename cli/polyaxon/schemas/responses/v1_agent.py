import datetime

from typing import Any, Dict, List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.lifecycle import V1Statuses
from polyaxon.schemas.base import BaseResponseModel


class V1Agent(BaseResponseModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    live_state: Optional[int]
    namespace: Optional[StrictStr]
    version_api: Optional[Dict[str, Any]]
    version: Optional[StrictStr]
    content: Optional[StrictStr]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    status: Optional[V1Statuses]
    is_replica: Optional[bool]
    is_ui_managed: Optional[bool]
    settings: Optional[Dict[str, Any]]
