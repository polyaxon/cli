from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_team import V1Team


class V1ListTeamsResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Team]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
