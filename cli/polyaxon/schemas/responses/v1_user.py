from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.email import EmailStr

from polyaxon.schemas.base import BaseResponseModel


class V1User(BaseResponseModel):
    username: Optional[StrictStr]
    email: Optional[EmailStr]
    name: Optional[StrictStr]
    kind: Optional[StrictStr]
    theme: Optional[int]
    organization: Optional[StrictStr]
