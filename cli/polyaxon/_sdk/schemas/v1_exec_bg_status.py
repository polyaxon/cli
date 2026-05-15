from datetime import datetime
from typing import Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ExecBgStatus(BaseAllowSchemaModel):
    """
    One background exec status record.
    """

    exec_id: Optional[StrictStr] = None
    pid: Optional[StrictInt] = None
    state: Optional[StrictStr] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[StrictInt] = None
    exit_code: Optional[StrictInt] = None
    signal: Optional[StrictStr] = None
    stdout_bytes: Optional[StrictInt] = None
    stderr_bytes: Optional[StrictInt] = None
    tag: Optional[StrictStr] = None
