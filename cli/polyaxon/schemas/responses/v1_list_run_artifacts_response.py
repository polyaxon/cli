from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from traceml.artifacts import V1RunArtifact


class V1ListRunArtifactsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1RunArtifact]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
