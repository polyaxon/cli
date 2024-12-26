from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1StatusCondition


class V1EntityNotificationBody(BaseAllowSchemaModel):
    namespace: Optional[StrictStr] = None
    owner: Optional[StrictStr] = None
    project: Optional[StrictStr] = None
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    condition: Optional[V1StatusCondition] = None
    connections: Optional[List[StrictStr]] = None
