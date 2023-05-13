from typing import Optional

from pydantic import StrictStr

from polyaxon.lifecycle import V1StageCondition
from polyaxon.schemas.base import BaseSchemaModel


class V1EntityStageBodyRequest(BaseSchemaModel):
    owner: Optional[StrictStr]
    entity: Optional[StrictStr]
    kind: Optional[StrictStr]
    name: Optional[StrictStr]
    condition: Optional[V1StageCondition]
