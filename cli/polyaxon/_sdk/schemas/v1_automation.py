import datetime

from typing import Any, Dict, List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.utils.enums import PEnum
from clipped.compact.pydantic import StrictInt


class AutomationTriggerKind(str, PEnum):
    """Type of trigger evaluation logic"""

    EVENT = "event"  # Simple event matching
    METRIC = "metric"  # Metric threshold triggers
    COMPOUND = "compound"  # AND/OR logic combining triggers
    SEQUENCE = "sequence"  # Events in specific order
    QUERY = "query"  # Scheduled query-based triggers


class AutomationTriggerPosture(str, PEnum):
    """When the trigger fires"""

    REACTIVE = "reactive"  # Fire when events happen
    PROACTIVE = "proactive"  # Fire when events DON'T happen (absence detection)


class AutomationTargetKind(str, PEnum):
    """Entity kinds for triggers and actions"""

    RUN = "run"
    COMPONENT = "component"
    MODEL = "model"
    ARTIFACT = "artifact"
    PROJECT = "project"
    CONNECTION = "connection"  # For integrations (Slack, webhook targets)
    WEBHOOK = "webhook"  # For incoming webhook sources
    ORG = "org"


class AutomationActionKind(str, PEnum):
    """Actions that can be performed"""

    # Notifications
    NOTIFY = "notify"  # Send notification via connection (Slack, Teams, Email)
    WEBHOOK = "webhook"  # Call external webhook URL

    # Run operations
    START = "start"  # Start a new run
    RESTART = "restart"  # Restart failed run
    RESUME = "resume"  # Resume paused run
    STOP = "stop"  # Stop running run
    SKIP = "skip"  # Skip pending run
    STATUS = "status"  # Update run status

    # Version operations
    PROMOTE = "promote"  # Promote run to version
    STAGE = "stage"  # Change stage

    # Lifecycle operations
    TRANSFER = "transfer"  # Transfer to run/version another project
    TAG = "tag"  # Add/remove tags
    ARCHIVE = "archive"  # Archive resource
    DELETE = "delete"  # Delete resource


class AutomationExecutionKind(str, PEnum):
    """When an action executes"""

    TRIGGER = "trigger"  # Execute when automation fires
    RESOLVE = "resolve"  # Execute when condition clears


class AutomationStateKind(str, PEnum):
    """
    Tracks whether an automation is currently in 'triggered' or 'normal' state.
    Used for resolve_action firing and preventing duplicate notifications.
    """

    NORMAL = "normal"
    TRIGGERED = "triggered"


class AutomationTriggerStateKind(str, PEnum):
    """Types of trigger state tracking."""

    BUCKET = "bucket"
    STATE = "state"
    SEQUENCE = "sequence"
    COMPOUND = "compound"


class AutomationExecutionStatus(str, PEnum):
    """Automation execution status"""

    PENDING = "pending"  # Waiting to be processed
    SCHEDULED = "scheduled"
    RUNNING = "running"  # Currently executing
    RETRYING = "retrying"  # Failed, will retry
    SUCCEEDED = "succeeded"  # Completed successfully
    FAILED = "failed"  # Failed permanently


class AutomationFailStrategy(str, PEnum):
    """How to handle action failures in automation execution"""

    STOP = "stop"  # Stop on first failure (default)
    CONTINUE = "continue"  # Continue all actions, report failures at end


class MetricTriggerConfigCondition(str, PEnum):
    """Comparison condition for metric values."""

    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"


# Trigger Config Schemas


class V1EventTriggerConfig(BaseAllowSchemaModel):
    """Configuration for EVENT triggers that fire on specific events."""

    threshold: Optional[int] = Field(
        default=1, description="Number of events required before firing"
    )
    within: Optional[int] = Field(
        default=None, description="Time window in seconds for threshold counting"
    )
    group_by: Optional[List[StrictStr]] = Field(
        default=None,
        description="Fields to group events by (e.g., ['run.uuid', 'project.uuid'])",
    )


class V1QueryTriggerConfig(BaseAllowSchemaModel):
    """Configuration for QUERY triggers that run PQL queries on schedule."""

    query: StrictStr = Field(description="PQL query to filter matching entities")
    threshold: Optional[int] = Field(
        default=1, description="Minimum matches required to fire"
    )
    aggregate: Optional[bool] = Field(
        default=False,
        description="If True, create single execution with all matches. If False, one execution per match.",
    )


class V1SequenceTriggerConfig(BaseAllowSchemaModel):
    """Configuration for SEQUENCE triggers that fire when events occur in order."""

    expect: List[StrictStr] = Field(
        description="Ordered list of event kinds to match (e.g., ['run.created', 'run.running', 'run.failed'])"
    )
    within: Optional[int] = Field(
        default=3600, description="Time window in seconds for all events to occur"
    )
    strict: Optional[bool] = Field(
        default=False,
        description="If True, resets progress if unexpected events occur",
    )
    group_by: Optional[List[StrictStr]] = Field(
        default=None,
        description="Fields to track sequences separately (e.g., ['run.uuid'])",
    )


class V1MetricTriggerConfig(BaseAllowSchemaModel):
    """Configuration for METRIC triggers that fire on metric threshold conditions."""

    metric: StrictStr = Field(
        description="Name of the metric to monitor (e.g., 'loss', 'accuracy')"
    )
    condition: MetricTriggerConfigCondition = Field(
        description="Comparison condition: above, below, equals, crosses_above, crosses_below"
    )
    threshold: float = Field(description="Threshold value to compare against")
    window_size: Optional[int] = Field(
        default=1, description="Number of recent values to average before comparison"
    )
    query: Optional[StrictStr] = Field(
        default=None, description="PQL filter to select which runs to monitor"
    )


class V1SubTriggerConfig(BaseAllowSchemaModel):
    """A sub-trigger within a compound trigger."""

    kind: AutomationTriggerKind = Field(
        description="Sub-trigger kind: event, query, metric, sequence, compound"
    )
    # Event sub-trigger fields
    expect: Optional[List[StrictStr]] = Field(
        default=None, description="Event kinds to match (for event sub-triggers)"
    )
    query: Optional[StrictStr] = Field(
        default=None, description="PQL query filter (for query sub-triggers)"
    )
    # Metric sub-trigger fields
    metric: Optional[StrictStr] = Field(
        default=None, description="Metric name (for metric sub-triggers)"
    )
    condition: Optional[StrictStr] = Field(
        default=None, description="Metric condition (for metric sub-triggers)"
    )
    threshold: Optional[Union[int, float]] = Field(
        default=None, description="Threshold value"
    )


class V1CompoundTriggerConfig(BaseAllowSchemaModel):
    """Configuration for COMPOUND triggers that combine multiple conditions."""

    require: Union[StrictStr, int] = Field(
        default="all",
        description="'all' (AND), 'any' (OR), or integer N for N-of-M matching",
    )
    within: Optional[int] = Field(
        default=600, description="Time window in seconds for sub-triggers to fire"
    )
    triggers: List[V1SubTriggerConfig] = Field(
        description="List of sub-triggers to evaluate"
    )


# Union kind for all trigger configs
TriggerConfig = Union[
    V1EventTriggerConfig,
    V1QueryTriggerConfig,
    V1SequenceTriggerConfig,
    V1MetricTriggerConfig,
    V1CompoundTriggerConfig,
]


class V1AutomationAction(BaseAllowSchemaModel):
    """An action to execute when an automation fires or resolves."""

    uuid: Optional[StrictStr] = None
    kind: Optional[AutomationExecutionKind] = None  # 'trigger' or 'resolve'
    priority: Optional[StrictInt] = None
    action: Optional[AutomationActionKind] = None  # AutomationActionKind
    apply_to: Optional[AutomationTargetKind] = (
        None  # AutomationTargetKind (target kind)
    )
    entity_uuid: Optional[StrictStr] = None  # Target entity UUID
    config: Optional[Dict[str, Any]] = None  # Action-specific config


class V1AutomationExecution(BaseAllowSchemaModel):
    uuid: Optional[StrictStr] = None
    automation: Optional[StrictStr] = None
    kind: Optional[AutomationExecutionKind] = None
    status: Optional[AutomationExecutionStatus] = None
    triggering_event: Optional[Dict[str, Any]] = None
    bucketing_key: Optional[Union[Dict[str, Any], StrictStr]] = None
    target_kind: Optional[StrictStr] = None
    target_uuid: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    started_at: Optional[datetime.datetime] = None
    finished_at: Optional[datetime.datetime] = None
    wait_time: Optional[float] = None
    duration: Optional[float] = None
    action_result: Optional[Dict[str, Any]] = None
    retry_count: Optional[StrictInt] = None


class V1Automation(BaseAllowSchemaModel):
    uuid: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    project: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    live_state: Optional[StrictInt] = None
    org_level: Optional[bool] = None
    enabled: Optional[bool] = None

    # Trigger configuration
    trigger_kind: Optional[AutomationTriggerKind] = None
    posture: Optional[AutomationTriggerPosture] = None
    trigger_on: Optional[AutomationTargetKind] = None
    trigger_entity_uuid: Optional[StrictStr] = None
    trigger_config: Optional[Dict[str, Any]] = None
    trigger_schedule: Optional[Dict[str, Any]] = None

    # Actions (via separate AutomationAction model)
    actions: Optional[List[V1AutomationAction]] = None

    # Execution behavior
    fail_strategy: Optional[StrictStr] = None  # AutomationFailStrategy
