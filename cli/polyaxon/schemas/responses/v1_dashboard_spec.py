from typing import List, Optional

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_section_spec import V1SectionSpec


class V1DashboardSpec(BaseResponseModel):
    sections: Optional[List[V1SectionSpec]]
