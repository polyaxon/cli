from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_tag import V1Tag


class V1ListTagsResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1Tag]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
