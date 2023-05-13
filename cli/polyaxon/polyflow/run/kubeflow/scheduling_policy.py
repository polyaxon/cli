from typing import Optional

from clipped.types.ref_or_obj import IntOrRef
from pydantic import Field, StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1SchedulingPolicy(BaseSchemaModel):
    _IDENTIFIER = "schedulingPolicy"

    min_available: Optional[IntOrRef] = Field(alias="minAvailable")
    queue: Optional[StrictStr]
    priority_class: Optional[StrictStr] = Field(alias="priorityClass")
