from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_agent import V1Agent


class V1ListAgentsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Agent]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
