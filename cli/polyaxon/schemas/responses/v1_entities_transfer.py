from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.uuids import UUIDStr

from polyaxon.schemas.base import BaseResponseModel


class V1EntitiesTransfer(BaseResponseModel):
    uuids: Optional[List[UUIDStr]]
    project: Optional[StrictStr]
