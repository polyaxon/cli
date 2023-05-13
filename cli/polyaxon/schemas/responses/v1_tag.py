from typing import Any, Dict, Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1Tag(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    color: Optional[StrictStr]
    description: Optional[StrictStr]
    icon: Optional[StrictStr]
    stats: Optional[Dict[str, Any]]
