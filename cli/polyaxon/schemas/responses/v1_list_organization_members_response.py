from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_organization_member import V1OrganizationMember


class V1ListOrganizationMembersResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1OrganizationMember]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
