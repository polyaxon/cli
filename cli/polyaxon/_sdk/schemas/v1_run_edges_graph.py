from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_run_edge_lineage import V1RunEdgeLineage


class V1RunEdgesGraph(BaseAllowSchemaModel):
    edges: Optional[List[V1RunEdgeLineage]]
