from typing import Optional

from clipped.types.email import EmailStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1UserSingup(BaseSchemaModel):
    username: Optional[StrictStr]
    email: Optional[EmailStr]
    organization: Optional[StrictStr]
    password: Optional[StrictStr]
    invitation_key: Optional[StrictStr]
