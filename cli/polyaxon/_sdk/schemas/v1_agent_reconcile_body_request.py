from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1AgentReconcileBodyRequest(BaseAllowSchemaModel):
    """
    V1AgentReconcileBodyRequest
    """

    owner: Optional[StrictStr] = None
    uuid: Optional[StrictStr] = None
    reconcile: Optional[Dict[str, Any]] = None
