from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.uuids import UUIDStr

from polyaxon.schemas.base import BaseResponseModel


class V1SettingsCatalog(BaseResponseModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
