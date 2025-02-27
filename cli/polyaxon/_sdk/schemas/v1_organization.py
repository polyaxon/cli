import datetime

from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1Organization(BaseAllowSchemaModel):
    user: Optional[StrictStr] = None
    user_email: Optional[EmailStr] = None
    name: Optional[StrictStr] = None
    is_public: Optional[bool] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    support_revoke_at: Optional[datetime.datetime] = None
    expiration: Optional[int] = None
    role: Optional[StrictStr] = None
    queue: Optional[StrictStr] = None
    default_presets: Optional[List[StrictStr]] = None
    default_presets_ordered: Optional[List[StrictStr]] = None
    is_cloud_viewable: Optional[bool] = None
    archived_deletion_interval: Optional[int] = None
    auth: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
