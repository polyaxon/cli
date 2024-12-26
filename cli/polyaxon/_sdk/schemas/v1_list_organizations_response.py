from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_organization import V1Organization


class V1ListOrganizationsResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[V1Organization]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
