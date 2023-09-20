from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1PasswordChange(BaseAllowSchemaModel):
    old_password: Optional[StrictStr]
    new_password1: Optional[StrictStr]
    new_password2: Optional[StrictStr]
