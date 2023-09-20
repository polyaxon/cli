from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.lifecycle import V1StatusCondition


class V1EntityNotificationBody(BaseAllowSchemaModel):
    namespace: Optional[StrictStr]
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    condition: Optional[V1StatusCondition]
    connections: Optional[List[StrictStr]]
