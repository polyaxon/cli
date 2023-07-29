from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_search import V1Search


class V1ListSearchesResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Search]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
