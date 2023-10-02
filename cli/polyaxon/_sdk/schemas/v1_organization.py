import datetime

from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1Organization(BaseAllowSchemaModel):
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
    archived_deletion_interval: Optional[int]
    auth: Optional[Dict[str, Any]]
    plan: Optional[Dict[str, Any]]
    usage: Optional[Dict[str, Any]]
