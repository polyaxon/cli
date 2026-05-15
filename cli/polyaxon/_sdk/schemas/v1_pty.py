from datetime import datetime
from typing import Optional

from clipped.compact.pydantic import StrictBool, StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1Pty(BaseAllowSchemaModel):
    """
    One PTY session record.
    """

    pty_id: Optional[StrictStr] = None
    pid: Optional[StrictInt] = None
    state: Optional[StrictStr] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[StrictInt] = None
    exit_code: Optional[StrictInt] = None
    signal: Optional[StrictStr] = None
    last_activity: Optional[datetime] = None
    last_client_activity: Optional[datetime] = None
    detached_since: Optional[datetime] = None
    attached: Optional[StrictBool] = None
    cols: Optional[StrictInt] = None
    rows: Optional[StrictInt] = None
    tag: Optional[StrictStr] = None
