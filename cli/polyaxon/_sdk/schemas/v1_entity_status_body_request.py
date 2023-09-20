from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1StatusCondition


class V1EntityStatusBodyRequest(BaseAllowSchemaModel):
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    uuid: Optional[UUIDStr]
    condition: Optional[V1StatusCondition]
    force: Optional[bool]
