from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_team_member import V1TeamMember


class V1ListTeamMembersResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[V1TeamMember]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
