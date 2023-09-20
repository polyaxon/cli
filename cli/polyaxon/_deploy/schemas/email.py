from typing import Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class EmailConfig(BaseSchemaModel):
    enabled: Optional[bool]
    email_from: Optional[StrictStr] = Field(alias="from")
    host: Optional[StrictStr]
    port: Optional[StrictInt]
    use_tls: Optional[bool] = Field(alias="useTls")
    host_user: Optional[StrictStr] = Field(alias="hostUser")
    host_password: Optional[StrictStr] = Field(alias="hostPassword")
    backend: Optional[StrictStr]
