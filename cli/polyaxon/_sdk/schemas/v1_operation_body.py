from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._flow import V1RunPending
from polyaxon._schemas.lifecycle import ManagedBy


class V1OperationBody(BaseAllowSchemaModel):
    content: Optional[StrictStr] = None
    is_managed: Optional[bool] = None
    managed_by: Optional[ManagedBy] = None
    pending: Optional[V1RunPending] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    meta_info: Optional[Dict[str, Any]] = None
