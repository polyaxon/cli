from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1PasswordChange(BaseAllowSchemaModel):
    old_password: Optional[StrictStr] = None
    new_password1: Optional[StrictStr] = None
    new_password2: Optional[StrictStr] = None
