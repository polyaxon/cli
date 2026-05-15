from datetime import datetime
from typing import Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1FsStatResult(BaseAllowSchemaModel):
    """
    Response body for GET /fs/stat.
    """

    path: Optional[StrictStr] = None
    type: Optional[StrictStr] = None
    size: Optional[StrictInt] = None
    mtime: Optional[datetime] = None
    mode: Optional[StrictStr] = None
    uid: Optional[StrictInt] = None
    gid: Optional[StrictInt] = None
    symlink_target: Optional[StrictStr] = None
