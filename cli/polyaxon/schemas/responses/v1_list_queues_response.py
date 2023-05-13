from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_queue import V1Queue


class V1ListQueuesResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Queue]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
