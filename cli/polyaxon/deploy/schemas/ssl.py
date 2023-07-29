from typing import Optional

from clipped.compact.pydantic import Field, StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class SSLConfig(BaseSchemaModel):
    enabled: Optional[bool]
    secret_name: Optional[StrictStr] = Field(alias="secretName")
    path: Optional[StrictStr]
