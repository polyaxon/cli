from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_run_edge import V1RunEdge


class V1ListRunEdgesResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1RunEdge]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
