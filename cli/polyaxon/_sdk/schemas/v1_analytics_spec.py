from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1AnalyticsSpec(BaseAllowSchemaModel):
    view: Optional[StrictStr]
    trunc: Optional[StrictStr]
    groupby: Optional[StrictStr]
    frequency: Optional[StrictStr]
