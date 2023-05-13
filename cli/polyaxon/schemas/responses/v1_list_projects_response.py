from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_project import V1Project


class V1ListProjectsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Project]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
