from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_organization_member import V1OrganizationMember


class V1ListOrganizationMembersResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1OrganizationMember]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
