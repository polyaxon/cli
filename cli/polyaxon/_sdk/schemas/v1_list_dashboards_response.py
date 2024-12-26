from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_dashboard import V1Dashboard


class V1ListDashboardsResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1Dashboard]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
