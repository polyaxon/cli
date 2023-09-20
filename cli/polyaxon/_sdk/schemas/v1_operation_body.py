from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._flow import V1RunPending
from polyaxon._schemas.lifecycle import ManagedBy


class V1OperationBody(BaseAllowSchemaModel):
    content: Optional[StrictStr]
    is_managed: Optional[bool]
    managed_by: Optional[ManagedBy]
    pending: Optional[V1RunPending]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    meta_info: Optional[Dict[str, Any]]
