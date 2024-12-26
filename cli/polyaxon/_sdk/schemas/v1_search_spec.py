from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_analytics_spec import V1AnalyticsSpec
from polyaxon._sdk.schemas.v1_dashboard_spec import V1DashboardSpec


class V1SearchSpec(BaseAllowSchemaModel):
    query: Optional[StrictStr] = None
    sort: Optional[StrictStr] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    groupby: Optional[StrictStr] = None
    columns: Optional[StrictStr] = None
    layout: Optional[StrictStr] = None
    sections: Optional[StrictStr] = None
    compares: Optional[StrictStr] = None
    heat: Optional[StrictStr] = None
    events: Optional[V1DashboardSpec] = None
    histograms: Optional[Dict[str, Any]] = None
    trends: Optional[Dict[str, Any]] = None
    analytics: Optional[V1AnalyticsSpec] = None
