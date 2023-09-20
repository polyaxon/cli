import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1ProjectVersionKind, V1StageCondition, V1Stages


class V1ProjectVersion(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    connection: Optional[StrictStr]
    run: Optional[StrictStr]
    artifacts: Optional[List[StrictStr]]
    meta_info: Optional[Dict[str, Any]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    stage: Optional[V1Stages]
    kind: Optional[V1ProjectVersionKind]
    stage_conditions: Optional[List[V1StageCondition]]
    content: Optional[StrictStr]
    readme: Optional[StrictStr]
    state: Optional[StrictStr]
    role: Optional[StrictStr]
    contributors: Optional[Dict[str, Any]]
