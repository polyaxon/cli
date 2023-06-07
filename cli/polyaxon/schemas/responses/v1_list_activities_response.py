from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_activity import V1Activity


class V1ListActivitiesResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Activity]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
