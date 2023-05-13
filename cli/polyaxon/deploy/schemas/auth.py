from typing import Optional

from pydantic import Field, StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class AuthConfig(BaseSchemaModel):
    enabled: Optional[bool]
    external: Optional[StrictStr]
    use_resolver: Optional[bool] = Field(alias="useResolver")
