from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1UserSingup(BaseAllowSchemaModel):
    username: Optional[StrictStr]
    email: Optional[EmailStr]
    organization: Optional[StrictStr]
    password: Optional[StrictStr]
    invitation_key: Optional[StrictStr]
