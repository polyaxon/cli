from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_token import V1Token


class V1ListTokenResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Token]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
