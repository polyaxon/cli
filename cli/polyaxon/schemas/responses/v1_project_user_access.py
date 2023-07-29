from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1ProjectUserAccess(BaseResponseModel):
    user: Optional[StrictStr]
    queue: Optional[StrictStr]
    preset: Optional[StrictStr]
