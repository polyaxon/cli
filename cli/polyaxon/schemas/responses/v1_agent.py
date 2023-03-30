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

import datetime

from typing import Any, Dict, List, Optional

from pydantic import StrictStr

from polyaxon.lifecycle import V1Statuses
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields import UUIDStr


class V1Agent(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    live_state: Optional[int]
    namespace: Optional[StrictStr]
    version_api: Optional[Dict[str, Any]]
    version: Optional[StrictStr]
    content: Optional[StrictStr]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    status: Optional[V1Statuses]
    is_replica: Optional[bool]
    is_ui_managed: Optional[bool]
    settings: Optional[Dict[str, Any]]
