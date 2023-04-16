#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import List, Union

from clipped.types.ref_or_obj import RefField
from clipped.utils.enums import PEnum
from pydantic import StrictStr

from polyaxon.contexts import refs as ctx_refs
from polyaxon.lifecycle import V1Statuses
from polyaxon.schemas.base import BaseSchemaModel


class V1EventKind(str, PEnum):
    RUN_STATUS_CREATED = "run_status_created"
    RUN_STATUS_RESUMING = "run_status_resuming"
    RUN_STATUS_COMPILED = "run_status_compiled"
    RUN_STATUS_ON_SCHEDULE = "run_status_on_schedule"
    RUN_STATUS_QUEUED = "run_status_queued"
    RUN_STATUS_SCHEDULED = "run_status_scheduled"
    RUN_STATUS_STARTING = "run_status_starting"
    RUN_STATUS_RUNNING = "run_status_running"
    RUN_STATUS_PROCESSING = "run_status_processing"
    RUN_STATUS_STOPPING = "run_status_stopping"
    RUN_STATUS_FAILED = "run_status_failed"
    RUN_STATUS_STOPPED = "run_status_stopped"
    RUN_STATUS_SUCCEEDED = "run_status_succeeded"
    RUN_STATUS_SKIPPED = "run_status_skipped"
    RUN_STATUS_WARNING = "run_status_warning"
    RUN_STATUS_UNSCHEDULABLE = "run_status_unschedulable"
    RUN_STATUS_UPSTREAM_FAILED = "run_status_upstream_failed"
    RUN_STATUS_RETRYING = "run_status_retrying"
    RUN_STATUS_UNKNOWN = "run_status_unknown"
    RUN_STATUS_DONE = "run_status_done"
    RUN_APPROVED_ACTOR = "run_approved_actor"
    RUN_INVALIDATED_ACTOR = "run_invalidated_actor"
    RUN_NEW_ARTIFACTS = "run_new_artifacts"
    CONNECTION_GIT_COMMIT = "connection_git_commit"
    CONNECTION_DATASET_VERSION = "connection_dataset_version"
    CONNECTION_REGISTRY_IMAGE = "connection_registry_image"
    ALERT_INFO = "alert_info"
    ALERT_WARNING = "alert_warning"
    ALERT_CRITICAL = "alert_critical"
    MODEL_VERSION_NEW_METRIC = "model_version_new_metric"
    PROJECT_CUSTOM_EVENT = "project_custom_event"
    ORG_CUSTOM_EVENT = "org_custom_event"

    @classmethod
    def get_events_statuses_mapping(cls):
        return {
            cls.RUN_STATUS_CREATED: V1Statuses.CREATED,
            cls.RUN_STATUS_RESUMING: V1Statuses.RESUMING,
            cls.RUN_STATUS_ON_SCHEDULE: V1Statuses.ON_SCHEDULE,
            cls.RUN_STATUS_COMPILED: V1Statuses.COMPILED,
            cls.RUN_STATUS_QUEUED: V1Statuses.QUEUED,
            cls.RUN_STATUS_SCHEDULED: V1Statuses.SCHEDULED,
            cls.RUN_STATUS_STARTING: V1Statuses.STARTING,
            cls.RUN_STATUS_RUNNING: V1Statuses.RUNNING,
            cls.RUN_STATUS_PROCESSING: V1Statuses.PROCESSING,
            cls.RUN_STATUS_STOPPING: V1Statuses.STOPPING,
            cls.RUN_STATUS_FAILED: V1Statuses.FAILED,
            cls.RUN_STATUS_STOPPED: V1Statuses.STOPPED,
            cls.RUN_STATUS_SUCCEEDED: V1Statuses.SUCCEEDED,
            cls.RUN_STATUS_SKIPPED: V1Statuses.SKIPPED,
            cls.RUN_STATUS_WARNING: V1Statuses.WARNING,
            cls.RUN_STATUS_UNSCHEDULABLE: V1Statuses.UNSCHEDULABLE,
            cls.RUN_STATUS_UPSTREAM_FAILED: V1Statuses.UPSTREAM_FAILED,
            cls.RUN_STATUS_RETRYING: V1Statuses.RETRYING,
            cls.RUN_STATUS_UNKNOWN: V1Statuses.UNKNOWN,
            cls.RUN_STATUS_DONE: V1Statuses.DONE,
        }


class V1EventTrigger(BaseSchemaModel, ctx_refs.RefMixin):
    """Events are an advanced triggering logic that users can take advantage of in addition to:
      * Manual triggers via API/CLI/UI.
      * Time-based triggers with schedules and crons.
      * Upstream triggers with upstream runs or upstream ops in DAGs.

    Events can be attached to an operation in the context of a DAG
    to extend the simple trigger process,
    this is generally important when the user defines a dependency between two operations
    and needs a run to start as soon as
    the upstream run generates an event instead of waiting until it reaches a final state.
    For instance, a usual use-case is to start a tensorboard as soon as training starts.
    In that case the downstream operation will watch for the `running` status.

    Events can be attached as well to a single operation
    to wait for an internal alert or external events,
    for instance if a user integrates Polyaxon with Github,
    they can trigger training as soon as Polyaxon is notified that a new git commit was created.

    Polyaxon provides several internal and external events that users
    can leverage to fully automate their usage of the platform:
      * "run_status_created"
      * "run_status_resuming"
      * "run_status_compiled"
      * "run_status_queued"
      * "run_status_scheduled"
      * "run_status_starting"
      * "run_status_initializing"
      * "run_status_running"
      * "run_status_processing"
      * "run_status_stopping"
      * "run_status_failed"
      * "run_status_stopped"
      * "run_status_succeeded"
      * "run_status_skipped"
      * "run_status_warning"
      * "run_status_unschedulable"
      * "run_status_upstream_failed"
      * "run_status_retrying"
      * "run_status_unknown"
      * "run_status_done"
      * "run_approved_actor"
      * "run_invalidated_actor"
      * "run_new_artifacts"
      * "connection_git_commit"
      * "connection_dataset_version"
      * "connection_registry_image"
      * "alert_info"
      * "alert_warning"
      * "alert_critical"
      * "model_version_new_metric"
      * "project_custom_event"
      * "org_custom_event"

    Args:
         kinds: List[str]
         ref: str

    > **Important**: Currently only events with prefix `run_status_*` are supported.

    ## YAML usage

    ```yaml
    >>> events:
    >>>   ref: {{ ops.upstream-operation }}
    >>>   kinds: [run_status_running]
    ```

    ```yaml
    >>> event:
    >>>   ref: {{ connections.git-repo-connection-name }}
    >>>   kinds: [connection_git_commit]
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1EventKind, V1EventTrigger
    >>> event1 = V1EventTrigger(
    >>>     ref="{{ ops.upstream-operation }}",
    >>>     kinds=[V1EventTrigger.RUN_STATUS_RUNNING],
    >>> )
    >>> event2 = V1EventTrigger(
    >>>     ref="{{ connections.git-repo-connection-name }}",
    >>>     kinds=[V1EventTrigger.CONNECTION_GIT_COMMIT],
    >>> )
    ```

    ## Fields

    ### kinds

    The trigger event kinds to watch, if any event is detected the operation defining the `events`
    section will be initiated.

    ```yaml
    >>> event:
    >>>   kinds: [run_status_running, run_status_done]
    ```

    > **Note**: Similar to trigger in DAGs, after an operation is initiated,
    > it will still have to validate the rest of the Polyaxonfile,
    > i.e. conditions, contexts, connections, ...

    ### ref

    A valid reference that Polyaxon can resolve the objects that will send the events to watch for.
    All supported events are prefixed with the object reference that can send such events.

    The `run_*` events can be referenced both by `runs.UUID` or
    `ops.OPERATION_NAME` if defined in the context of a DAG.

    ```yaml
    >>> event:
    >>>   ref: ops.upstream_operation_name
    ```
    """

    _IDENTIFIER = "event_trigger"

    kinds: List[Union[V1EventKind, RefField]]
    ref: StrictStr
