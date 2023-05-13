from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_run import V1Run


class V1ListRunsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Run]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
