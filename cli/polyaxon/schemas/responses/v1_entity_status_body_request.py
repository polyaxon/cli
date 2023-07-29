from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.uuids import UUIDStr

from polyaxon.lifecycle import V1StatusCondition
from polyaxon.schemas.base import BaseResponseModel


class V1EntityStatusBodyRequest(BaseResponseModel):
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    uuid: Optional[UUIDStr]
    condition: Optional[V1StatusCondition]
    force: Optional[bool]
