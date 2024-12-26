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
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    user: Optional[StrictStr] = None
    owner: Optional[StrictStr] = None
    project: Optional[StrictStr] = None
    schedule_at: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    started_at: Optional[datetime.datetime] = None
    finished_at: Optional[datetime.datetime] = None
    wait_time: Optional[float] = None
    duration: Optional[float] = None
    managed_by: Optional[ManagedBy] = None
    is_managed: Optional[bool] = None
    is_approved: Optional[bool] = None
    pending: Optional[V1RunPending] = None
    content: Optional[StrictStr] = None
    raw_content: Optional[StrictStr] = None
    status: Optional[V1Statuses] = None
    bookmarked: Optional[bool] = None
    live_state: Optional[int] = None
    readme: Optional[StrictStr] = None
    meta_info: Optional[Dict[str, Any]] = None
    kind: Optional[V1RunKind] = None
    runtime: Optional[Union[V1RunKind, V1MatrixKind, V1ScheduleKind]] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    original: Optional[V1Cloning] = None
    pipeline: Optional[V1Pipeline] = None
    status_conditions: Optional[List[V1StatusCondition]] = None
    role: Optional[StrictStr] = None
    contributors: Optional[List[Dict[str, Any]]] = None
    settings: Optional[V1RunSettings] = None
    resources: Optional[V1RunResources] = None
    graph: Optional[Dict[str, Any]] = None
    merge: Optional[bool] = None
