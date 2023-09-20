from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_connection_response import V1ConnectionResponse


class V1ListConnectionsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1ConnectionResponse]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
