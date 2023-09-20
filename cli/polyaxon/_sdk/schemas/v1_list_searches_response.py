from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_search import V1Search


class V1ListSearchesResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Search]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
