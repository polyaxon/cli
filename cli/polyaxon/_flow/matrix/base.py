from typing import Optional

from clipped.compact.pydantic import Field, StrictStr
from polyaxon._schemas.base import BaseSchemaModel


class BaseSearchConfig(BaseSchemaModel):
    _USE_DISCRIMINATOR = True

    name_suffix: Optional[StrictStr] = Field(alias="nameSuffix", default=None)

    def create_iteration(self, **kwargs) -> int:
        return 0

    def should_reschedule(self, **kwargs) -> bool:
        return False
