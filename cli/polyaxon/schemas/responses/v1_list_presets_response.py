from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_preset import V1Preset


class V1ListPresetsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Preset]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
