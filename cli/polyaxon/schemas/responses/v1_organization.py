import datetime

from typing import Any, Dict, Optional

from clipped.types.email import EmailStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1Organization(BaseSchemaModel):
    user: Optional[StrictStr]
    user_email: Optional[EmailStr]
    name: Optional[StrictStr]
    is_public: Optional[bool]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    support_revoke_at: Optional[datetime.datetime]
    expiration: Optional[int]
    role: Optional[StrictStr]
    queue: Optional[StrictStr]
    preset: Optional[StrictStr]
    is_cloud_viewable: Optional[bool]
    auth: Optional[Dict[str, Any]]
    plan: Optional[Dict[str, Any]]
    usage: Optional[Dict[str, Any]]
