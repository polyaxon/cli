from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.email import EmailStr


class V1TrialStart(BaseAllowSchemaModel):
    name: Optional[StrictStr]
    email: Optional[EmailStr]
    organization: Optional[StrictStr]
    plan: Optional[StrictStr]
    seats: Optional[int]
    details: Optional[Dict[str, Any]]
