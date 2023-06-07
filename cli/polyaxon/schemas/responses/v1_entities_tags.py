from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1EntitiesTags(BaseResponseModel):
    uuids: Optional[List[UUIDStr]]
    tags: Optional[List[StrictStr]]
