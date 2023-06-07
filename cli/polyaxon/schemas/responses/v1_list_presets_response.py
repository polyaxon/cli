from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_preset import V1Preset


class V1ListPresetsResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Preset]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
