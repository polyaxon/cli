from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_organization import V1Organization


class V1ListOrganizationsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1Organization]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
