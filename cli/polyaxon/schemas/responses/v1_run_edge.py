from typing import Any, Dict, List, Optional

from polyaxon.lifecycle import V1Statuses
from polyaxon.polyflow.run.kinds import V1RunEdgeKind
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_run import V1Run


class V1RunEdge(BaseSchemaModel):
    upstream: Optional[V1Run]
    downstream: Optional[V1Run]
    kind: Optional[V1RunEdgeKind]
    values: Optional[Dict[str, Any]]
    statuses: Optional[List[V1Statuses]]
