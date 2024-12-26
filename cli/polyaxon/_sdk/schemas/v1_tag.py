from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1Tag(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    color: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    icon: Optional[StrictStr] = None
    stats: Optional[Dict[str, Any]] = None
