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

from typing import Optional, List

from polyaxon.schemas.base import BaseSchemaModel


class V1AgentStateResponseAgentState(BaseSchemaModel):
    schedules: Optional[List]
    hooks: Optional[List]
    watchdogs: Optional[List]
    tuners: Optional[List]
    queued: Optional[List]
    stopping: Optional[List]
    deleting: Optional[List]
    apply: Optional[List]
    checks: Optional[List]
    full: Optional[bool]
