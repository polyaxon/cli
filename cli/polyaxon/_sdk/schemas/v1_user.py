from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1User(BaseAllowSchemaModel):
    username: Optional[StrictStr]
    email: Optional[StrictStr]
    name: Optional[StrictStr]
    kind: Optional[StrictStr]
    theme: Optional[int]
    organization: Optional[StrictStr]
