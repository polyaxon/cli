from typing import Any, Dict, List, Optional

from pydantic import StrictStr

from polyaxon.lifecycle import ManagedBy
from polyaxon.schemas import V1RunPending
from polyaxon.schemas.base import BaseResponseModel


class V1OperationBody(BaseResponseModel):
    content: Optional[StrictStr]
    is_managed: Optional[bool]
    managed_by: Optional[ManagedBy]
    pending: Optional[V1RunPending]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    meta_info: Optional[Dict[str, Any]]
