from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1PasswordChange(BaseResponseModel):
    old_password: Optional[StrictStr]
    new_password1: Optional[StrictStr]
    new_password2: Optional[StrictStr]
