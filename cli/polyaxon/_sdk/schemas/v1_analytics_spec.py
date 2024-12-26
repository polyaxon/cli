from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1AnalyticsSpec(BaseAllowSchemaModel):
    view: Optional[StrictStr] = None
    trunc: Optional[StrictStr] = None
    groupby: Optional[StrictStr] = None
    frequency: Optional[StrictStr] = None
