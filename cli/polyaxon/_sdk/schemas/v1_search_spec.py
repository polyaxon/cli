from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_analytics_spec import V1AnalyticsSpec
from polyaxon._sdk.schemas.v1_dashboard_spec import V1DashboardSpec


class V1SearchSpec(BaseAllowSchemaModel):
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
