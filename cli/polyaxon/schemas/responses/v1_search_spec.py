from typing import Any, Dict, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel
from polyaxon.schemas.responses.v1_analytics_spec import V1AnalyticsSpec
from polyaxon.schemas.responses.v1_dashboard_spec import V1DashboardSpec


class V1SearchSpec(BaseResponseModel):
    query: Optional[StrictStr]
    sort: Optional[StrictStr]
    limit: Optional[int]
    offset: Optional[int]
    groupby: Optional[StrictStr]
    columns: Optional[StrictStr]
    layout: Optional[StrictStr]
    sections: Optional[StrictStr]
    compares: Optional[StrictStr]
    heat: Optional[StrictStr]
    events: Optional[V1DashboardSpec]
    histograms: Optional[Dict[str, Any]]
    trends: Optional[Dict[str, Any]]
    analytics: Optional[V1AnalyticsSpec]
