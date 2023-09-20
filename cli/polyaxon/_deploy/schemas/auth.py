from typing import Optional

from clipped.compact.pydantic import Field, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class AuthConfig(BaseSchemaModel):
    enabled: Optional[bool]
    external: Optional[StrictStr]
    use_resolver: Optional[bool] = Field(alias="useResolver")
