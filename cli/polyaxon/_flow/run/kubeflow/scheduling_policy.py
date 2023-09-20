from typing import Optional

from clipped.compact.pydantic import Field, StrictStr
from clipped.types.ref_or_obj import IntOrRef

from polyaxon._schemas.base import BaseSchemaModel


class V1SchedulingPolicy(BaseSchemaModel):
    _IDENTIFIER = "schedulingPolicy"

    min_available: Optional[IntOrRef] = Field(alias="minAvailable")
    queue: Optional[StrictStr]
    priority_class: Optional[StrictStr] = Field(alias="priorityClass")
