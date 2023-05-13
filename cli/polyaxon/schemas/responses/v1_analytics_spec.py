from typing import Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1AnalyticsSpec(BaseSchemaModel):
    view: Optional[StrictStr]
    trunc: Optional[StrictStr]
    groupby: Optional[StrictStr]
    frequency: Optional[StrictStr]
