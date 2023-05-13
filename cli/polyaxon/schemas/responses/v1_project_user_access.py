from typing import Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1ProjectUserAccess(BaseSchemaModel):
    user: Optional[StrictStr]
    queue: Optional[StrictStr]
    preset: Optional[StrictStr]
