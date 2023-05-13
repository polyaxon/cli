from typing import Any, Dict, Optional

from clipped.types.email import EmailStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1TrialStart(BaseSchemaModel):
    name: Optional[StrictStr]
    email: Optional[EmailStr]
    organization: Optional[StrictStr]
    plan: Optional[StrictStr]
    seats: Optional[int]
    details: Optional[Dict[str, Any]]
