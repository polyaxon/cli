from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1UserSingup(BaseAllowSchemaModel):
    username: Optional[StrictStr] = None
    email: Optional[EmailStr] = None
    organization: Optional[StrictStr] = None
    password: Optional[StrictStr] = None
    invitation_key: Optional[StrictStr] = None
