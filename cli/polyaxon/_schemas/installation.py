from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1Installation(BaseAllowSchemaModel):
    key: Optional[StrictStr]
    version: Optional[StrictStr]
    dist: Optional[StrictStr]
    host: Optional[StrictStr]
    hmac: Optional[StrictStr]
    mode: Optional[StrictStr]
    org: Optional[bool]
    auth: Optional[List[StrictStr]]
