from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from traceml.artifacts import V1RunArtifact


class V1ListRunArtifactsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1RunArtifact]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
