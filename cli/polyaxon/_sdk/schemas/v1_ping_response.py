from datetime import datetime
from typing import Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1PingResponse(BaseAllowSchemaModel):
    """
    Response body for GET /ping.
    """

    status: Optional[StrictStr] = None
    version: Optional[StrictStr] = None
    uptime_ms: Optional[StrictInt] = None
    last_activity: Optional[datetime] = None
    execs_running: Optional[StrictInt] = None
    ptys_running: Optional[StrictInt] = None
    ptys_attached: Optional[StrictInt] = None
