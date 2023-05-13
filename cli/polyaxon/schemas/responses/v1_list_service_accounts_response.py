from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_service_account import V1ServiceAccount


class V1ListServiceAccountsResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[V1ServiceAccount]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
