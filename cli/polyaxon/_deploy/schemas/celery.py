from typing import Optional

from clipped.compact.pydantic import Field, StrictInt

from polyaxon._schemas.base import BaseSchemaModel


class CeleryConfig(BaseSchemaModel):
    enabled: Optional[bool]
    task_track_started: Optional[bool] = Field(alias="taskTrackStarted")
    broker_pool_limit: Optional[StrictInt] = Field(alias="brokerPoolLimit")
    confirm_publish: Optional[bool] = Field(alias="confirmPublish")
    worker_prefetch_multiplier: Optional[StrictInt] = Field(
        alias="workerPrefetchMultiplier"
    )
    worker_max_tasks_per_child: Optional[StrictInt] = Field(
        alias="workerMaxTasksPerChild"
    )
    worker_max_memory_per_child: Optional[StrictInt] = Field(
        alias="workerMaxMemoryPerChild"
    )
    task_always_eager: Optional[bool] = Field(alias="taskAlwaysEager")
