from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._schemas.lifecycle import V1StageCondition


class V1EntityStageBodyRequest(BaseAllowSchemaModel):
    owner: Optional[StrictStr] = None
    entity: Optional[StrictStr] = None
    kind: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    condition: Optional[V1StageCondition] = None
