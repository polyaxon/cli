from typing import Optional

from clipped.types.email import EmailStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1UserSingup(BaseResponseModel):
    username: Optional[StrictStr]
    email: Optional[EmailStr]
    organization: Optional[StrictStr]
    password: Optional[StrictStr]
    invitation_key: Optional[StrictStr]
