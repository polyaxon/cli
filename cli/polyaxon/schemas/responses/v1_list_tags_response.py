from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_tag import V1Tag


class V1ListTagsResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Tag]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
