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

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.lifecycle import V1StatusCondition, V1Statuses
from polyaxon.polyflow.run.kinds import V1RunKind
from polyaxon.polyflow.run.resources import V1RunResources
from polyaxon.schemas import V1RunPending
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_cloning import V1Cloning
from polyaxon.schemas.responses.v1_pipeline import V1Pipeline
from polyaxon.schemas.responses.v1_run_settings import V1RunSettings


class V1Run(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    user: Optional[StrictStr]
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    schedule_at: Optional[datetime.datetime]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    started_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]
    wait_time: Optional[int]
    duration: Optional[int]
    is_managed: Optional[bool]
    is_approved: Optional[bool]
    pending: Optional[V1RunPending]
    content: Optional[StrictStr]
    raw_content: Optional[StrictStr]
    status: Optional[V1Statuses]
    bookmarked: Optional[bool]
    live_state: Optional[int]
    readme: Optional[StrictStr]
    meta_info: Optional[Dict[str, Any]]
    kind: Optional[V1RunKind]
    runtime: Optional[V1RunKind]
    inputs: Optional[Dict[str, Any]]
    outputs: Optional[Dict[str, Any]]
    original: Optional[V1Cloning]
    pipeline: Optional[V1Pipeline]
    status_conditions: Optional[List[V1StatusCondition]]
    role: Optional[StrictStr]
    settings: Optional[V1RunSettings]
    resources: Optional[V1RunResources]
    graph: Optional[Dict[str, Any]]
    merge: Optional[bool]
