from datetime import datetime
from typing import Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1FsEntry(BaseAllowSchemaModel):
    """
    One filesystem list entry.
    """

    name: Optional[StrictStr] = None
    type: Optional[StrictStr] = None
    size: Optional[StrictInt] = None
    mtime: Optional[datetime] = None
    mode: Optional[StrictStr] = None
    symlink_target: Optional[StrictStr] = None
