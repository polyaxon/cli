import datetime

from typing import Any, Dict, List, Optional, Union

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._flow import (
    V1MatrixKind,
    V1RunKind,
    V1RunPending,
    V1RunResources,
    V1ScheduleKind,
)
from polyaxon._schemas.lifecycle import ManagedBy, V1StatusCondition, V1Statuses
from polyaxon._sdk.schemas.v1_cloning import V1Cloning
from polyaxon._sdk.schemas.v1_pipeline import V1Pipeline
from polyaxon._sdk.schemas.v1_run_settings import V1RunSettings


class V1Run(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    user: Optional[StrictStr]
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    schedule_at: Optional[datetime.datetime]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    started_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]
    wait_time: Optional[float]
    duration: Optional[float]
    managed_by: Optional[ManagedBy]
    is_managed: Optional[bool]
    is_approved: Optional[bool]
    pending: Optional[V1RunPending]
    content: Optional[StrictStr]
    raw_content: Optional[StrictStr]
    status: Optional[V1Statuses]
    bookmarked: Optional[bool]
    live_state: Optional[int]
    readme: Optional[StrictStr]
    meta_info: Optional[Dict[str, Any]]
    kind: Optional[V1RunKind]
    runtime: Optional[Union[V1RunKind, V1MatrixKind, V1ScheduleKind]]
    inputs: Optional[Dict[str, Any]]
    outputs: Optional[Dict[str, Any]]
    original: Optional[V1Cloning]
    pipeline: Optional[V1Pipeline]
    status_conditions: Optional[List[V1StatusCondition]]
    role: Optional[StrictStr]
    contributors: Optional[Dict[str, Any]]
    settings: Optional[V1RunSettings]
    resources: Optional[V1RunResources]
    graph: Optional[Dict[str, Any]]
    merge: Optional[bool]
