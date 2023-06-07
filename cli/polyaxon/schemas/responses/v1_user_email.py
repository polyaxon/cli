from typing import Optional

from clipped.types.email import EmailStr

from polyaxon.schemas.base import BaseResponseModel


class V1UserEmail(BaseResponseModel):
    email: Optional[EmailStr]
