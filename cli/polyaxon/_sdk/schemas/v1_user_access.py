from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1UserAccess(BaseAllowSchemaModel):
    user: Optional[StrictStr]
    queue: Optional[StrictStr]
    preset: Optional[StrictStr]
    namespace: Optional[StrictStr]
