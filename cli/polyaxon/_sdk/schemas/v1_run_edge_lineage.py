from typing import Any, Dict, Optional

from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr


class V1RunEdgeLineage(BaseAllowSchemaModel):
    """
    V1RunEdgeLineage
    """

    uuid: Optional[UUIDStr] = None
    is_upstream: Optional[bool] = None
    values: Optional[Dict[str, Any]] = None
