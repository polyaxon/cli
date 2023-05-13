from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_run_connection import V1RunConnection


class V1ListRunConnectionsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1RunConnection]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
