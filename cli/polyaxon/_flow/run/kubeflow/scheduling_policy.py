from typing import Optional

from clipped.compact.pydantic import Field, StrictStr
from clipped.types.ref_or_obj import IntOrRef

from polyaxon._schemas.base import BaseSchemaModel


class V1SchedulingPolicy(BaseSchemaModel):
    """Scheduling policy for Kubeflow distributed runs.

    Args:
        min_available: int, optional
        queue: str, optional
        priority_class: str, optional
    """

    _IDENTIFIER = "schedulingPolicy"

    min_available: Optional[IntOrRef] = Field(alias="minAvailable")
    queue: Optional[StrictStr]
    priority_class: Optional[StrictStr] = Field(alias="priorityClass")
