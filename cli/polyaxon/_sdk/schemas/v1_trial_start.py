from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1TrialStart(BaseAllowSchemaModel):
    name: Optional[StrictStr] = None
    email: Optional[EmailStr] = None
    organization: Optional[StrictStr] = None
    plan: Optional[StrictStr] = None
    seats: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
