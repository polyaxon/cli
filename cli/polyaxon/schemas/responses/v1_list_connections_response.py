from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_connection_response import V1ConnectionResponse


class V1ListConnectionsResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1ConnectionResponse]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
