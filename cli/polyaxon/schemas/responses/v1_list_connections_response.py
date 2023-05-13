from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_connection_response import V1ConnectionResponse


class V1ListConnectionsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1ConnectionResponse]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
