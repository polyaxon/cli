from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1UserAccessData(BaseAllowSchemaModel):
    username: Optional[StrictStr]
    is_sa: Optional[bool]


class V1UserAccess(BaseAllowSchemaModel):
    user: Optional[StrictStr]
    user_data: Optional[V1UserAccessData]
    queue: Optional[StrictStr]
    preset: Optional[StrictStr]
    namespace: Optional[StrictStr]
