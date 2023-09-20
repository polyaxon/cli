from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Uuids(BaseAllowSchemaModel):
    uuids: Optional[List[UUIDStr]]
