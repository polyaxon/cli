from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._schemas.lifecycle import V1StageCondition


class V1EntityStageBodyRequest(BaseAllowSchemaModel):
    owner: Optional[StrictStr]
    entity: Optional[StrictStr]
    kind: Optional[StrictStr]
    name: Optional[StrictStr]
    condition: Optional[V1StageCondition]
