from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_preset import V1Preset


class V1ListPresetsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Preset]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
