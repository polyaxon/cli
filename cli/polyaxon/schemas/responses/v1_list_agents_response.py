from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_agent import V1Agent


class V1ListAgentsResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Agent]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
