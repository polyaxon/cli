from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_project_version import V1ProjectVersion


class V1ListProjectVersionsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1ProjectVersion]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
