from typing import Optional

from clipped.compact.pydantic import Field, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class SSLConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    secret_name: Optional[StrictStr] = Field(alias="secretName", default=None)
    path: Optional[StrictStr] = None
