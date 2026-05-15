from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ExecRequest(BaseAllowSchemaModel):
    """
    Request body for POST /exec.
    """

    command: Optional[List[StrictStr]] = None
    env: Optional[Dict[str, Any]] = None
    workdir: Optional[StrictStr] = None
    stdin: Optional[StrictStr] = None
    timeout_ms: Optional[StrictInt] = None
