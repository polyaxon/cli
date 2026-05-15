from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1FsPathResult(BaseAllowSchemaModel):
    """
    Response body for filesystem path operations.
    """

    path: Optional[StrictStr] = None
