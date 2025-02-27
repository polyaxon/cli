from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1UserAccessData(BaseAllowSchemaModel):
    username: Optional[StrictStr] = None
    is_sa: Optional[bool] = None


class V1UserAccess(BaseAllowSchemaModel):
    user: Optional[StrictStr] = None
    user_data: Optional[V1UserAccessData] = None
    queue: Optional[StrictStr] = None
    default_presets: Optional[List[StrictStr]] = None
    default_presets_ordered: Optional[List[StrictStr]] = None
    namespace: Optional[StrictStr] = None
