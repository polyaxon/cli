from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from traceml.artifacts import V1RunArtifact


class V1ListRunArtifactsResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1RunArtifact]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
