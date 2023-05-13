from typing import List, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1EntitiesTags(BaseSchemaModel):
    uuids: Optional[List[UUIDStr]]
    tags: Optional[List[StrictStr]]
