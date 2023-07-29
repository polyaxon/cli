from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_queue import V1Queue


class V1ListQueuesResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Queue]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
