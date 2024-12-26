from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_team_member import V1TeamMember


class V1ListTeamMembersResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1TeamMember]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
