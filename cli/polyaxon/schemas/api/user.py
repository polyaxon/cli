from typing import Optional

from clipped.types.email import EmailStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class UserConfig(BaseSchemaModel):
    _IDENTIFIER = "user"

    username: StrictStr
    email: Optional[EmailStr]
    name: Optional[StrictStr]
    theme: Optional[int]
