from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1AnalyticsSpec(BaseResponseModel):
    view: Optional[StrictStr]
    trunc: Optional[StrictStr]
    groupby: Optional[StrictStr]
    frequency: Optional[StrictStr]
