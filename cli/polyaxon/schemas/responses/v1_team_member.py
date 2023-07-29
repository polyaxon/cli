import datetime

from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.email import EmailStr

from polyaxon.schemas.base import BaseResponseModel


class V1TeamMember(BaseResponseModel):
    user: Optional[StrictStr]
    user_email: Optional[EmailStr]
    role: Optional[StrictStr]
    org_role: Optional[StrictStr]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
