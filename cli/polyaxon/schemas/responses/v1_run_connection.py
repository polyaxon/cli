from typing import Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1RunConnection(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    kind: Optional[StrictStr]
