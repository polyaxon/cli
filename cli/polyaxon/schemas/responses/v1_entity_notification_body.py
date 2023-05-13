from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.lifecycle import V1StatusCondition
from polyaxon.schemas.base import BaseSchemaModel


class V1EntityNotificationBody(BaseSchemaModel):
    namespace: Optional[StrictStr]
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    condition: Optional[V1StatusCondition]
    connections: Optional[List[StrictStr]]
