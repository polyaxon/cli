from typing import Any, Dict, Optional

from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._schemas.lifecycle import V1Statuses
from polyaxon._sdk.schemas.v1_agent_state_response_agent_state import (
    V1AgentStateResponseAgentState,
)


class V1AgentStateResponse(BaseAllowSchemaModel):
    status: Optional[V1Statuses]
    state: Optional[V1AgentStateResponseAgentState]
    live_state: Optional[int]
    compatible_updates: Optional[Dict[str, Any]]
