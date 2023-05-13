from typing import Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1Auth(BaseSchemaModel):
    token: Optional[StrictStr]
