from typing import List, Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from polyaxon._sdk.schemas.v1_automation import V1AutomationExecution


class V1ListAutomationExecutionsResponse(BaseAllowSchemaModel):
    """
    V1ListAutomationExecutionsResponse
    """

    count: Optional[StrictInt] = None
    results: Optional[List[V1AutomationExecution]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
