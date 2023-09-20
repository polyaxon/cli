from typing import Optional

from clipped.compact.pydantic import Field, StrictInt

from polyaxon._schemas.base import BaseSchemaModel


class IntervalsConfig(BaseSchemaModel):
    runs_scheduler: Optional[StrictInt] = Field(alias="runsScheduler")
    operations_default_retry_delay: Optional[StrictInt] = Field(
        alias="operationsDefaultRetryDelay"
    )
    operations_max_retry_delay: Optional[StrictInt] = Field(
        alias="operationsMaxRetryDelay"
    )
    compatibility_check: Optional[StrictInt] = Field(alias="compatibilityCheck")
