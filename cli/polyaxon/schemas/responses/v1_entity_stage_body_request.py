from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.lifecycle import V1StageCondition
from polyaxon.schemas.base import BaseResponseModel


class V1EntityStageBodyRequest(BaseResponseModel):
    owner: Optional[StrictStr]
    entity: Optional[StrictStr]
    kind: Optional[StrictStr]
    name: Optional[StrictStr]
    condition: Optional[V1StageCondition]
