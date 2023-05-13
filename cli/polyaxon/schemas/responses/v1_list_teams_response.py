from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_team import V1Team


class V1ListTeamsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Team]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
