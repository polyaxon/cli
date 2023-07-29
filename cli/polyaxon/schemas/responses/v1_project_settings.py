from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_project_user_access import V1ProjectUserAccess


class V1ProjectSettings(BaseResponseModel):
    connections: Optional[List[StrictStr]]
    preset: Optional[StrictStr]
    presets: Optional[List[StrictStr]]
    queue: Optional[StrictStr]
    queues: Optional[List[StrictStr]]
    agents: Optional[List[StrictStr]]
    user_accesses: Optional[List[V1ProjectUserAccess]]
    teams: Optional[List[StrictStr]]
    projects: Optional[List[StrictStr]]
