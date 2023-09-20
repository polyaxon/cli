from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_organization_member import V1OrganizationMember


class V1ListOrganizationMembersResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1OrganizationMember]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
