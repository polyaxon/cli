from typing import Optional

from clipped.compact.pydantic import Field, StrictStr
from clipped.types.ref_or_obj import IntOrRef

from polyaxon._schemas.base import BaseSchemaModel


class V1SchedulingPolicy(BaseSchemaModel):
    """Scheduling policy for Kubeflow distributed runs.

    Args:
        min_available: int, optional
        queue: str, optional
        min_resources: int, optional
        priority_class: str, optional
        schedule_timeout_seconds: int, optional
    """

    _IDENTIFIER = "schedulingPolicy"

    min_available: Optional[IntOrRef] = Field(alias="minAvailable")
    queue: Optional[StrictStr]
    min_resources: Optional[IntOrRef] = Field(alias="minResources")
    priority_class: Optional[StrictStr] = Field(alias="priorityClass")
    schedule_timeout_seconds: Optional[IntOrRef] = Field(alias="scheduleTimeoutSeconds")
