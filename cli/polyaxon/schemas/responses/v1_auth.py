from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1Auth(BaseAllowSchemaModel):
    token: Optional[StrictStr]
