from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_agent import V1Agent


class V1ListAgentsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Agent]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
