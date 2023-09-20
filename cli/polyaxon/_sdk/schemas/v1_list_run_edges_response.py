from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_run_edge import V1RunEdge


class V1ListRunEdgesResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1RunEdge]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
