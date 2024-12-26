import datetime

from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1TeamMember(BaseAllowSchemaModel):
    user: Optional[StrictStr] = None
    user_email: Optional[EmailStr] = None
    role: Optional[StrictStr] = None
    org_role: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
