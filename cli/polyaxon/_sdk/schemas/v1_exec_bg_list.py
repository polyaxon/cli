from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel
from polyaxon._sdk.schemas.v1_exec_bg_status import V1ExecBgStatus


class V1ExecBgList(BaseAllowSchemaModel):
    """
    List response for GET /exec/bg.
    """

    execs: Optional[List[V1ExecBgStatus]] = None
