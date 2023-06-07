from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1EntitiesTransfer(BaseResponseModel):
    uuids: Optional[List[UUIDStr]]
    project: Optional[StrictStr]
