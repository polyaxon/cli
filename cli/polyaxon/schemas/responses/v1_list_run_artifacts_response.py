from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from traceml.artifacts import V1RunArtifact


class V1ListRunArtifactsResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1RunArtifact]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
