import datetime

from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1OrganizationMember(BaseAllowSchemaModel):
    user: Optional[StrictStr] = None
    user_email: Optional[EmailStr] = None
    role: Optional[StrictStr] = None
    kind: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
