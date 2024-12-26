from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_project_version import V1ProjectVersion


class V1ListProjectVersionsResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1ProjectVersion]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
