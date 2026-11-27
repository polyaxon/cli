from typing import Optional

from clipped.compact.pydantic import NAME_REGEX, StrictStr, constr
from clipped.types.email import EmailStr
from polyaxon._schemas.base import BaseSchemaModel


class RootUserConfig(BaseSchemaModel):
    username: Optional[constr(pattern=NAME_REGEX)] = None  # type: ignore[valid-type]
    password: Optional[StrictStr] = None
    email: Optional[EmailStr] = None
