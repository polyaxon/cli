from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_token import V1Token


class V1ListTokenResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1Token]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
