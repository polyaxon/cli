from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1User(BaseAllowSchemaModel):
    username: Optional[StrictStr] = None
    email: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    kind: Optional[StrictStr] = None
    theme: Optional[int] = None
    organization: Optional[StrictStr] = None
