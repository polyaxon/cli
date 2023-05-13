from typing import Optional

from clipped.types.uuids import UUIDStr
from pydantic import StrictStr

from polyaxon.polyflow.run.kinds import V1PipelineKind
from polyaxon.schemas.base import BaseSchemaModel


class V1Pipeline(BaseSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    kind: Optional[V1PipelineKind]
