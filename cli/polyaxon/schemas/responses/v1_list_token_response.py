from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_token import V1Token


class V1ListTokenResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Token]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
