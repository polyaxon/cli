from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.uuids import UUIDStr

from polyaxon.polyflow import V1CloningKind
from polyaxon.schemas.base import BaseResponseModel


class V1Cloning(BaseResponseModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    kind: Optional[V1CloningKind]
