from typing import Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.lifecycle import V1StatusCondition
from polyaxon.schemas.base import BaseSchemaModel


class V1EntityStatusBodyRequest(BaseSchemaModel):
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    uuid: Optional[UUIDStr]
    condition: Optional[V1StatusCondition]
    force: Optional[bool]
