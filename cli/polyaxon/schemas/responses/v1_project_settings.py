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
from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_project_user_access import V1ProjectUserAccess


class V1ProjectSettings(BaseSchemaModel):
    connections: Optional[List[StrictStr]]
    preset: Optional[StrictStr]
    presets: Optional[List[StrictStr]]
    queue: Optional[StrictStr]
    queues: Optional[List[StrictStr]]
    agents: Optional[List[StrictStr]]
    user_accesses: Optional[List[V1ProjectUserAccess]]
    teams: Optional[List[StrictStr]]
    projects: Optional[List[StrictStr]]
