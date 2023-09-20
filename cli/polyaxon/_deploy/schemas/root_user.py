from typing import Optional

from clipped.compact.pydantic import StrictStr, constr
from clipped.types.email import EmailStr

from polyaxon._schemas.base import NAME_REGEX, BaseSchemaModel


class RootUserConfig(BaseSchemaModel):
    username: Optional[constr(regex=NAME_REGEX)]  # type: ignore[valid-type]
    password: Optional[StrictStr]
    email: Optional[EmailStr]
