from typing import List, Optional

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_section_spec import V1SectionSpec


class V1DashboardSpec(BaseSchemaModel):
    sections: Optional[List[V1SectionSpec]]
