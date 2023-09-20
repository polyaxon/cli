from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_team import V1Team


class V1ListTeamsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Team]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
