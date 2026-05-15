from typing import Optional

from clipped.compact.pydantic import StrictBool, StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ExecBgLogs(BaseAllowSchemaModel):
    """
    Response body for GET /exec/bg/{id}/logs.
    """

    exec_id: Optional[StrictStr] = None
    stream: Optional[StrictStr] = None
    offset: Optional[StrictInt] = None
    next_offset: Optional[StrictInt] = None
    bytes: Optional[StrictInt] = None
    data: Optional[StrictStr] = None
    eof: Optional[StrictBool] = None
    state: Optional[StrictStr] = None
