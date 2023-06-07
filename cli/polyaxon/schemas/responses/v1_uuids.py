from typing import List, Optional

from clipped.types.uuids import UUIDStr

from polyaxon.schemas.base import BaseResponseModel


class V1Uuids(BaseResponseModel):
    uuids: Optional[List[UUIDStr]]
