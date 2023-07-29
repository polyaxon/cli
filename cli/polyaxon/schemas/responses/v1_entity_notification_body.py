from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.uuids import UUIDStr

from polyaxon.lifecycle import V1StatusCondition
from polyaxon.schemas.base import BaseResponseModel


class V1EntityNotificationBody(BaseResponseModel):
    namespace: Optional[StrictStr]
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    condition: Optional[V1StatusCondition]
    connections: Optional[List[StrictStr]]
