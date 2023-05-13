from typing import Optional

from clipped.types.email import EmailStr

from polyaxon.schemas.base import BaseSchemaModel


class V1UserEmail(BaseSchemaModel):
    email: Optional[EmailStr]
