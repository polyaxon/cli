from typing import Optional

from clipped.compact.pydantic import StrictBool, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1FsMkdirRequest(BaseAllowSchemaModel):
    """
    Request body for POST /fs/mkdir.
    """

    path: Optional[StrictStr] = None
    parents: Optional[StrictBool] = None
    mode: Optional[StrictStr] = None
