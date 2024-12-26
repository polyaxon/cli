from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1StatusCondition


class V1AgentStatusBodyRequest(BaseAllowSchemaModel):
    owner: Optional[StrictStr] = None
    uuid: Optional[UUIDStr] = None
    condition: Optional[V1StatusCondition] = None
