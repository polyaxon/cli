from typing import Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.polyflow import V1CloningKind
from polyaxon.schemas.base import BaseSchemaModel


class V1Cloning(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    kind: Optional[V1CloningKind]
