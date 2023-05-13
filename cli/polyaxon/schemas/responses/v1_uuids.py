from typing import List, Optional

from clipped.types.uuids import UUIDStr

from polyaxon.schemas.base import BaseSchemaModel


class V1Uuids(BaseSchemaModel):
    uuids: Optional[List[UUIDStr]]
