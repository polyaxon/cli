from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_section_spec import V1SectionSpec


class V1DashboardSpec(BaseAllowSchemaModel):
    xaxis: Optional[str] = None
    smoothing: Optional[int] = None
    ignore_outliers: Optional[bool] = None
    sample_size: Optional[int] = None
    sections: Optional[List[V1SectionSpec]] = None
