from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_organization import V1Organization


class V1ListOrganizationsResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1Organization]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
