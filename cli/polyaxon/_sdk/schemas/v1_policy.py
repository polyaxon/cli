import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from polyaxon._sdk.schemas.v1_user_access import V1UserAccess


class V1Policy(BaseAllowSchemaModel):
    uuid: Optional[StrictStr] = None
    owner: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    user: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    excluded_features: Optional[List[StrictStr]] = None
    excluded_runtimes: Optional[List[StrictStr]] = None
    archived_deletion_interval: Optional[int] = None
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
    connected_projects: Optional[List[StrictStr]] = None
