from typing import Optional

from clipped.compact.pydantic import Field, StrictInt

from polyaxon._schemas.base import BaseSchemaModel


class IntervalsConfig(BaseSchemaModel):
    compatibility_check: Optional[StrictInt] = Field(
        alias="compatibilityCheck", default=None
    )
