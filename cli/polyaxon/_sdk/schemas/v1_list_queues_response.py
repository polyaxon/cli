from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_queue import V1Queue


class V1ListQueuesResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Queue]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
