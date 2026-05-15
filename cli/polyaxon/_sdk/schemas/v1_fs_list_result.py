from typing import List, Optional

from clipped.compact.pydantic import StrictBool, StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from polyaxon._sdk.schemas.v1_fs_entry import V1FsEntry


class V1FsListResult(BaseAllowSchemaModel):
    """
    Response body for GET /fs/ls.
    """

    path: Optional[StrictStr] = None
    entries: Optional[List[V1FsEntry]] = None
    truncated: Optional[StrictBool] = None
