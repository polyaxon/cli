from typing import Optional

from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1UserEmail(BaseAllowSchemaModel):
    email: Optional[EmailStr]
