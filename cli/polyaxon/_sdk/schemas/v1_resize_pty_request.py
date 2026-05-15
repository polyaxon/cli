from typing import Optional

from clipped.compact.pydantic import StrictInt
from clipped.config.schema import BaseAllowSchemaModel


class V1ResizePtyRequest(BaseAllowSchemaModel):
    """
    Request body for POST /pty/{id}/resize.
    """

    cols: Optional[StrictInt] = None
    rows: Optional[StrictInt] = None
