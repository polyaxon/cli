from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_section_spec import V1SectionSpec


class V1DashboardSpec(BaseAllowSchemaModel):
    sections: Optional[List[V1SectionSpec]]
