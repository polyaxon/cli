from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_user_access import V1UserAccess


class V1ProjectSettings(BaseAllowSchemaModel):
    connections: Optional[List[StrictStr]] = None
    default_presets: Optional[List[StrictStr]] = None
    default_presets_ordered: Optional[List[StrictStr]] = None
    presets: Optional[List[StrictStr]] = None
    queue: Optional[StrictStr] = None
    queues: Optional[List[StrictStr]] = None
    agents: Optional[List[StrictStr]] = None
    namespaces: Optional[List[StrictStr]] = None
    user_accesses: Optional[List[V1UserAccess]] = None
    teams: Optional[List[StrictStr]] = None
    projects: Optional[List[StrictStr]] = None
    policy: Optional[StrictStr] = None
