from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel


class V1AgentStateResponseAgentState(BaseAllowSchemaModel):
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
