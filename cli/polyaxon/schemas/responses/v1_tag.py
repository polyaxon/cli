from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Tag(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    color: Optional[StrictStr]
    description: Optional[StrictStr]
    icon: Optional[StrictStr]
    stats: Optional[Dict[str, Any]]
