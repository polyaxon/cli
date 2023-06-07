from typing import Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1RunConnection(BaseResponseModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    kind: Optional[StrictStr]
