from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel


class V1AgentStateResponseAgentState(BaseAllowSchemaModel):
    schedules: Optional[List] = None
    hooks: Optional[List] = None
    watchdogs: Optional[List] = None
    tuners: Optional[List] = None
    queued: Optional[List] = None
    stopping: Optional[List] = None
    deleting: Optional[List] = None
    apply: Optional[List] = None
    checks: Optional[List] = None
    full: Optional[bool] = None
