from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_search import V1Search


class V1ListSearchesResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Search]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
