from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_project_version import V1ProjectVersion


class V1ListProjectVersionsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1ProjectVersion]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
