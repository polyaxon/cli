from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._flow import V1PipelineKind


class V1Pipeline(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    kind: Optional[V1PipelineKind]
