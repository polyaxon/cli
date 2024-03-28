from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_section_spec import V1SectionSpec


class V1DashboardSpec(BaseAllowSchemaModel):
    xaxis: Optional[str]
    smoothing: Optional[int]
    ignore_outliers: Optional[bool]
    sample_size: Optional[int]
    sections: Optional[List[V1SectionSpec]]
