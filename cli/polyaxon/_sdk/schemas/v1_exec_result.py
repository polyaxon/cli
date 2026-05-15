from typing import Optional

from clipped.compact.pydantic import StrictBool, StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ExecResult(BaseAllowSchemaModel):
    """
    Response body for POST /exec.
    """

    exec_id: Optional[StrictStr] = None
    exit_code: Optional[StrictInt] = None
    signal: Optional[StrictStr] = None
    stdout: Optional[StrictStr] = None
    stderr: Optional[StrictStr] = None
    duration_ms: Optional[StrictInt] = None
    timed_out: Optional[StrictBool] = None
    stdout_truncated: Optional[StrictBool] = None
    stderr_truncated: Optional[StrictBool] = None
