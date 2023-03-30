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

from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields import UUIDStr
from polyaxon.schemas.responses.v1_project_settings import V1ProjectSettings


class V1Project(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    owner: Optional[StrictStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    is_public: Optional[bool]
    bookmarked: Optional[bool]
    readme: Optional[StrictStr]
    excluded_features: Optional[List[StrictStr]]
    excluded_runtimes: Optional[List[StrictStr]]
    settings: Optional[V1ProjectSettings]
    role: Optional[StrictStr]
    live_state: Optional[int]
