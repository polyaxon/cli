from typing import Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class EmailConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    email_from: Optional[StrictStr] = Field(alias="from", default=None)
    host: Optional[StrictStr] = None
    port: Optional[StrictInt] = None
    use_tls: Optional[bool] = Field(alias="useTls", default=None)
    host_user: Optional[StrictStr] = Field(alias="hostUser", default=None)
    host_password: Optional[StrictStr] = Field(alias="hostPassword", default=None)
    backend: Optional[StrictStr] = None
