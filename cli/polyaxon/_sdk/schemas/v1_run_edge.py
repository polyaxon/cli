from typing import Any, Dict, List, Optional

from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._flow import V1RunEdgeKind
from polyaxon._schemas.lifecycle import V1Statuses
from polyaxon._sdk.schemas.v1_run import V1Run


class V1RunEdge(BaseAllowSchemaModel):
    upstream: Optional[V1Run] = None
    downstream: Optional[V1Run] = None
    kind: Optional[V1RunEdgeKind] = None
    values: Optional[Dict[str, Any]] = None
    statuses: Optional[List[V1Statuses]] = None
