from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_project import V1Project


class V1ListProjectsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Project]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
