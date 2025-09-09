import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1ProjectVersionKind, V1StageCondition, V1Stages


class V1ProjectVersion(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    owner: Optional[StrictStr] = None
    project: Optional[StrictStr] = None
    user: Optional[StrictStr] = None
    connection: Optional[StrictStr] = None
    run: Optional[StrictStr] = None
    artifacts: Optional[List[StrictStr]] = None
    meta_info: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    stage: Optional[V1Stages] = None
    kind: Optional[V1ProjectVersionKind] = None
    stage_conditions: Optional[List[V1StageCondition]] = None
    content: Optional[StrictStr] = None
    readme: Optional[StrictStr] = None
    state: Optional[StrictStr] = None
    role: Optional[StrictStr] = None
    contributors: Optional[List[Dict[str, Any]]] = None
