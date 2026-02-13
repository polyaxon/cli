from typing import Any, Dict, Optional
from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1AutomationTestRequest(BaseAllowSchemaModel):
    """
    V1AutomationTestRequest
    """

    owner: Optional[StrictStr] = None
    automation_uuid: Optional[StrictStr] = None
    event: Optional[Dict[str, Any]] = None
