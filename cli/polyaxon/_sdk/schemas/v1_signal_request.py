from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1SignalRequest(BaseAllowSchemaModel):
    """
    Request body for signal endpoints.
    """

    signal: Optional[StrictStr] = None
