from typing import Optional

from clipped.compact.pydantic import Field, StrictInt

from polyaxon._schemas.base import BaseSchemaModel


class CeleryConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    task_track_started: Optional[bool] = Field(alias="taskTrackStarted", default=None)
    broker_pool_limit: Optional[StrictInt] = Field(
        alias="brokerPoolLimit", default=None
    )
    confirm_publish: Optional[bool] = Field(alias="confirmPublish", default=None)
    worker_prefetch_multiplier: Optional[StrictInt] = Field(
        alias="workerPrefetchMultiplier", default=None
    )
    worker_max_tasks_per_child: Optional[StrictInt] = Field(
        alias="workerMaxTasksPerChild", default=None
    )
    worker_max_memory_per_child: Optional[StrictInt] = Field(
        alias="workerMaxMemoryPerChild", default=None
    )
    task_always_eager: Optional[bool] = Field(alias="taskAlwaysEager", default=None)
