from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1User(BaseAllowSchemaModel):
    username: Optional[StrictStr]
    email: Optional[EmailStr]
    name: Optional[StrictStr]
    kind: Optional[StrictStr]
    theme: Optional[int]
    organization: Optional[StrictStr]
