import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_dashboard_spec import V1DashboardSpec


class V1Dashboard(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    user: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    live_state: Optional[int] = None
    spec: Optional[V1DashboardSpec] = None
    org_level: Optional[bool] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
