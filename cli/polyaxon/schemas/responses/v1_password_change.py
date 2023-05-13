from typing import Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1PasswordChange(BaseSchemaModel):
    old_password: Optional[StrictStr]
    new_password1: Optional[StrictStr]
    new_password2: Optional[StrictStr]
