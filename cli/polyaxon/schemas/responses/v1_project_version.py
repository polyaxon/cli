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

from polyaxon.lifecycle import V1ProjectVersionKind, V1StageCondition, V1Stages
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields import UUIDStr


class V1ProjectVersion(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    connection: Optional[StrictStr]
    run: Optional[StrictStr]
    artifacts: Optional[List[StrictStr]]
    meta_info: Optional[Dict[str, Any]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    stage: Optional[V1Stages]
    kind: Optional[V1ProjectVersionKind]
    stage_conditions: Optional[List[V1StageCondition]]
    content: Optional[StrictStr]
    readme: Optional[StrictStr]
    state: Optional[StrictStr]
    role: Optional[StrictStr]
