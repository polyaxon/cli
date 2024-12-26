from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1EntitiesTransfer(BaseAllowSchemaModel):
    uuids: Optional[List[UUIDStr]] = None
    project: Optional[StrictStr] = None
