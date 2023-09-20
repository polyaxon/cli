from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_service_account import V1ServiceAccount


class V1ListServiceAccountsResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[V1ServiceAccount]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
