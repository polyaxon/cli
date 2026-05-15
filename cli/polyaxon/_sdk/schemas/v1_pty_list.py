from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel
from polyaxon._sdk.schemas.v1_pty import V1Pty


class V1PtyList(BaseAllowSchemaModel):
    """
    List response for GET /pty.
    """

    sessions: Optional[List[V1Pty]] = None
