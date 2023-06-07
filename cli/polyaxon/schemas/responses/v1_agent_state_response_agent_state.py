from typing import List, Optional

from polyaxon.schemas.base import BaseResponseModel


class V1AgentStateResponseAgentState(BaseResponseModel):
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
