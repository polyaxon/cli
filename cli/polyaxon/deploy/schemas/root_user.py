from typing import Optional

from clipped.types.email import EmailStr
from pydantic import StrictStr, constr

from polyaxon.schemas.base import NAME_REGEX, BaseSchemaModel


class RootUserConfig(BaseSchemaModel):
    username: Optional[constr(regex=NAME_REGEX)]  # type: ignore[valid-type]
    password: Optional[StrictStr]
    email: Optional[EmailStr]
