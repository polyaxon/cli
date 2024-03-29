from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_run import V1Run


class V1ListRunsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Run]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
