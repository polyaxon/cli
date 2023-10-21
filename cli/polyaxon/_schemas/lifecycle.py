import datetime

from typing import Any, Dict, List, Optional, Union

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.utils.dates import parse_datetime
from clipped.utils.enums import PEnum
from clipped.utils.tz import now

from polyaxon._schemas.base import BaseSchemaModel


class V1Stages(str, PEnum):
    """Stage is the information that represents the current stage of an entity's version.

    You can describe what stage a component or a model version is at.

    The supported stages by Polyaxon.

    Enum:
        TESTING: "testing"
        STAGING: "staging"
        PRODUCTION: "production"
        DISABLED: "disabled"
    """

    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DISABLED = "disabled"


class V1Statuses(str, PEnum):
    """Status is the information that represents the current state of a run.

    By examining a run status and/or the history of its statuses,
    you can learn what stage the run is at, and what stages are left.

    The supported statuses by Polyaxon.

    Enum:
        CREATED: "created"
        ON_SCHEDULE: "on_schedule"
        RESUMING: "resuming"
        WARNING: "warning"
        UNSCHEDULABLE: "unschedulable"
        COMPILED: "compiled"
        QUEUED: "queued"
        SCHEDULED: "scheduled"
        STARTING: "starting"
        RUNNING: "running"
        SUCCEEDED: "succeeded"
        FAILED: "failed"
        UPSTREAM_FAILED: "upstream_failed"
        STOPPING: "stopping"
        STOPPED: "stopped"
        SKIPPED: "skipped"
        RETRYING: "retrying"
        UNKNOWN: "unknown"
    """

    CREATED = "created"
    RESUMING = "resuming"
    ON_SCHEDULE = "on_schedule"
    COMPILED = "compiled"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    STARTING = "starting"
    RUNNING = "running"
    PROCESSING = "processing"
    STOPPING = "stopping"
    FAILED = "failed"
    STOPPED = "stopped"
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    WARNING = "warning"
    UNSCHEDULABLE = "unschedulable"
    UPSTREAM_FAILED = "upstream_failed"
    RETRYING = "retrying"
    UNKNOWN = "unknown"
    DONE = "done"

    @classmethod
    def get_allowable_hook_values(cls):
        return {
            cls.FAILED,
            cls.STOPPED,
            cls.SUCCEEDED,
            cls.SKIPPED,
            cls.UPSTREAM_FAILED,
            cls.DONE,
        }


class StatusColor:
    """The statuses colors.

    Enum:
        GREEN: #1aaa55
        RED: #aa310f
        BLUE: #2e77aa
        YELLOW: #aa9e4a
        GREY: #485563
    """

    GREEN = "#1aaa55"
    RED = "#aa310f"
    BLUE = "#2e77aa"
    YELLOW = "#aa9e4a"
    GREY = "#485563"

    @classmethod
    def get_color(cls, status: str) -> str:
        if status in [V1Statuses.FAILED, V1Statuses.UPSTREAM_FAILED]:
            return cls.RED

        if status in [V1Statuses.SUCCEEDED, V1Statuses.SKIPPED]:
            return cls.GREEN

        if status == V1Statuses.STOPPED:
            return cls.GREY

        if LifeCycle.is_done(status):
            return cls.GREY

        return cls.YELLOW


class LifeCycle:
    """The Run LifeCycle is state machine for status transition."""

    WARNING_VALUES = {V1Statuses.UNSCHEDULABLE, V1Statuses.WARNING}
    ALL_WARNING_VALUES = WARNING_VALUES | {V1Statuses.UNKNOWN}
    SAFE_STOP_VALUES = {
        V1Statuses.CREATED,
        V1Statuses.ON_SCHEDULE,
        V1Statuses.RESUMING,
        V1Statuses.COMPILED,
    }
    PENDING_VALUES = {
        V1Statuses.CREATED,
        V1Statuses.ON_SCHEDULE,
        V1Statuses.RESUMING,
    }
    COMPILABLE_VALUES = PENDING_VALUES | {V1Statuses.RETRYING}
    ALL_PENDING_VALUES = COMPILABLE_VALUES | {V1Statuses.COMPILED, V1Statuses.QUEUED}
    RUNNING_VALUES = {
        V1Statuses.SCHEDULED,
        V1Statuses.STARTING,
        V1Statuses.PROCESSING,
        V1Statuses.RUNNING,
    }
    ON_K8S_VALUES = RUNNING_VALUES | ALL_WARNING_VALUES
    DONE_VALUES = {
        V1Statuses.FAILED,
        V1Statuses.UPSTREAM_FAILED,
        V1Statuses.STOPPED,
        V1Statuses.SKIPPED,
        V1Statuses.SUCCEEDED,
    }
    DONE_OR_IN_PROGRESS_VALUES = DONE_VALUES | {
        V1Statuses.STOPPING,
    }

    @classmethod
    def can_check_heartbeat(cls, status: str) -> bool:
        """Checks if a run with this status is in a state that allows to check for a heartbeat."""
        return status in cls.RUNNING_VALUES

    @classmethod
    def is_unschedulable(cls, status: str) -> bool:
        """Checks if a run with this status is unschedulable."""
        return status == V1Statuses.UNSCHEDULABLE

    @classmethod
    def is_processing(cls, status: str) -> bool:
        """Checks if a run with this status is processing."""
        return status == V1Statuses.PROCESSING

    @classmethod
    def is_warning(cls, status: str) -> bool:
        """Checks if a run with this status is in a warning status."""
        return status in cls.WARNING_VALUES

    @classmethod
    def is_pending(cls, status: str) -> bool:
        """Checks if a run with this status is in a pending status."""
        return status in cls.PENDING_VALUES

    @classmethod
    def is_compiled(cls, status: str) -> bool:
        """Checks if a run with this status is compiled."""
        return status == V1Statuses.COMPILED

    @classmethod
    def is_compilable(cls, status: str) -> bool:
        """Checks if a run with this status is compilable."""
        return status in cls.COMPILABLE_VALUES

    @classmethod
    def is_queued(cls, status: str) -> bool:
        """Checks if a run with this status is queued."""
        return status == V1Statuses.QUEUED

    @classmethod
    def is_starting(cls, status: str) -> bool:
        """Checks if a run with this status is starting."""
        return status == V1Statuses.STARTING

    @classmethod
    def is_running(cls, status: str) -> bool:
        """Checks if a run with this status is running."""
        return status in cls.RUNNING_VALUES

    @classmethod
    def is_unknown(cls, status: str) -> bool:
        """Checks if a run with this status is in an unknown state."""
        return status == V1Statuses.UNKNOWN

    @classmethod
    def is_safe_stoppable(cls, status: str) -> bool:
        """Checks if a run with this status is an be stopped without operator."""
        return status in cls.SAFE_STOP_VALUES

    @classmethod
    def is_k8s_stoppable(cls, status: str) -> bool:
        """Checks if a run with this status is scheduled on k8s and is stoppable."""
        return status in cls.ON_K8S_VALUES

    @classmethod
    def is_stoppable(cls, status: str) -> bool:
        """Checks if a run with this status is stoppable."""
        return not cls.is_done(status)

    @classmethod
    def is_stopping(cls, status: str) -> bool:
        """Checks if a run with this status is stopping."""
        return status == V1Statuses.STOPPING

    @classmethod
    def is_done(cls, status: str, progressing: bool = False) -> bool:
        """Checks if a run with this status is done."""
        if progressing:
            return status in cls.DONE_OR_IN_PROGRESS_VALUES

        return status in cls.DONE_VALUES

    @classmethod
    def failed(cls, status: str) -> bool:
        """Checks if a run with this status is failed."""
        return status == V1Statuses.FAILED or status == V1Statuses.UPSTREAM_FAILED

    @classmethod
    def succeeded(cls, status: str) -> bool:
        """Checks if a run with this status is succeeded."""
        return status == V1Statuses.SUCCEEDED

    @classmethod
    def stopped(cls, status: str) -> bool:
        """Checks if a run with this status is stopped."""
        return status == V1Statuses.STOPPED

    @classmethod
    def skipped(cls, status: str) -> bool:
        """Checks if a run with this status is skipped."""
        return status == V1Statuses.SKIPPED

    @classmethod
    def set_started_at(cls, entity) -> bool:
        # We allow to override started_at if the value is running
        if entity.started_at is not None:
            return False

        if cls.is_running(entity.status):
            entity.started_at = now()
            # Update wait_time
            if entity.wait_time is None:
                entity.wait_time = round(
                    (entity.started_at - entity.created_at).total_seconds(), 2
                )
            return True

        return False

    @classmethod
    def set_finished_at(cls, entity) -> bool:
        if cls.is_done(entity.status) and entity.finished_at is None:
            entity.finished_at = now()
            if entity.started_at is None:  # We should not have this case
                entity.started_at = entity.created_at
            # Update duration
            if entity.duration is None:
                entity.duration = round(
                    (entity.finished_at - entity.started_at).total_seconds(), 2
                )
            return True
        return False


class BaseCondition(BaseAllowSchemaModel):
    @classmethod
    def get_condition(
        cls,
        type=None,  # noqa
        status=None,
        last_update_time=None,
        last_transition_time=None,
        reason=None,
        message=None,
        meta_info=None,
    ):
        current_time = now()
        last_update_time = last_update_time or current_time
        last_transition_time = last_transition_time or current_time
        return cls(
            type=type.lower() if type else type,
            status=status,
            last_update_time=last_update_time,
            last_transition_time=last_transition_time,
            reason=reason,
            message=message,
            meta_info=meta_info,
        )

    def __eq__(self, other):
        return self.type == other.type and self.status == other.status

    @classmethod
    def get_last_update_time(cls, value):
        return parse_datetime(value)


class V1StatusCondition(BaseCondition):
    type: Optional[V1Statuses]
    status: Optional[Union[bool, str]]
    reason: Optional[StrictStr]
    message: Optional[StrictStr]
    last_update_time: Optional[datetime.datetime]
    last_transition_time: Optional[datetime.datetime]
    meta_info: Optional[Dict[str, Any]]


class V1Status(BaseSchemaModel):
    uuid: Optional[StrictStr]
    status: Optional[V1Statuses]
    status_conditions: Optional[List[V1StatusCondition]]
    meta_info: Optional[Dict[str, Any]]


class V1StageCondition(BaseCondition):
    type: Optional[V1Stages]
    status: Optional[Union[bool, str]]
    reason: Optional[StrictStr]
    message: Optional[StrictStr]
    last_update_time: Optional[datetime.datetime]
    last_transition_time: Optional[datetime.datetime]
    meta_info: Optional[Dict[str, Any]]


class V1Stage(BaseSchemaModel):
    uuid: Optional[StrictStr]
    stage: Optional[V1Stages]
    stage_conditions: Optional[List[V1StageCondition]]


class V1ProjectVersionKind(str, PEnum):
    COMPONENT = "component"
    MODEL = "model"
    ARTIFACT = "artifact"


class V1ProjectFeature(str, PEnum):
    COMPONENT = "component"
    MODEL = "model"
    ARTIFACT = "artifact"
    RUNTIME = "runtime"


class LiveState(int, PEnum):
    """State of a model in Polyaxon.

    Enum:
        LIVE: 1
        ARCHIVED: 0
        DELETION_PROGRESSING: -1
    """

    LIVE = 1
    ARCHIVED = 0
    DELETION_PROGRESSING = -1


class ManagedBy(str, PEnum):
    """Operator Managing a run in Polyaxon."""

    USER = "user"
    CLI = "cli"
    AGENT = "agent"

    @classmethod
    def is_managed(cls, value: str) -> bool:
        return value in {cls.CLI, cls.AGENT}
