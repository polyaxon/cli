from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_dashboard import V1Dashboard


class V1ListDashboardsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Dashboard]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
