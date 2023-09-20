from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.email import EmailStr

from polyaxon._schemas.base import BaseSchemaModel


class UserConfig(BaseSchemaModel):
    _IDENTIFIER = "user"

    username: StrictStr
    email: Optional[EmailStr]
    name: Optional[StrictStr]
    theme: Optional[int]
