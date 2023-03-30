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

from polyaxon.lifecycle import V1Statuses
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_agent_state_response_agent_state import (
    V1AgentStateResponseAgentState,
)


class V1AgentStateResponse(BaseSchemaModel):
    status: Optional[V1Statuses]
    state: Optional[V1AgentStateResponseAgentState]
    live_state: Optional[int]
    compatible_updates: Optional[Dict[str, Any]]
