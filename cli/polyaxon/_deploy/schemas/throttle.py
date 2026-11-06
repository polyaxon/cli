from typing import Dict, Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from polyaxon._schemas.base import BaseSchemaModel


class ThrottleConfig(BaseSchemaModel):
    rates: Optional[Dict[StrictStr, StrictInt]] = None
