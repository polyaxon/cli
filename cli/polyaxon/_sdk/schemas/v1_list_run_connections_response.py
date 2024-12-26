from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_run_connection import V1RunConnection


class V1ListRunConnectionsResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1RunConnection]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
