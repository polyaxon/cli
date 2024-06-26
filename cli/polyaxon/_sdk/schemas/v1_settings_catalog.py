from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1SettingsCatalog(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    version: Optional[StrictStr]
    url: Optional[StrictStr]
