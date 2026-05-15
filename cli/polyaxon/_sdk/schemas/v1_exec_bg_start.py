from datetime import datetime
from typing import Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ExecBgStart(BaseAllowSchemaModel):
    """
    Response body for POST /exec/bg.
    """

    exec_id: Optional[StrictStr] = None
    pid: Optional[StrictInt] = None
    started_at: Optional[datetime] = None
    tag: Optional[StrictStr] = None
