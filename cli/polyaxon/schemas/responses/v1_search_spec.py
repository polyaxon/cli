#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Dict, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_analytics_spec import V1AnalyticsSpec
from polyaxon.schemas.responses.v1_dashboard_spec import V1DashboardSpec


class V1SearchSpec(BaseSchemaModel):
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
