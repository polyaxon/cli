from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_activity import V1Activity


class V1ListActivitiesResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1Activity]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
