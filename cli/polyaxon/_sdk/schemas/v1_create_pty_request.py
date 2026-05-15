from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1CreatePtyRequest(BaseAllowSchemaModel):
    """
    Request body for POST /pty.
    """

    command: Optional[List[StrictStr]] = None
    env: Optional[Dict[str, Any]] = None
    workdir: Optional[StrictStr] = None
    cols: Optional[int] = None
    rows: Optional[int] = None
    tag: Optional[StrictStr] = None
