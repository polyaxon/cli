from typing import Optional
from typing_extensions import Literal

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import BoolOrRef, DatetimeOrRef, IntOrRef, TimeDeltaOrRef

from polyaxon._flow.schedules.enums import V1ScheduleKind
from polyaxon._schemas.base import BaseSchemaModel


class V1IntervalSchedule(BaseSchemaModel):
    """Interval schedules is an interface to trigger components following a frequency.

    Args:
        kind: str, should be equal to `interval`
        start_at: datetime, optional
        end_at: datetime, optional
        max_runs: int, optional
        frequency: int, required
        depends_on_past: bool, optional


    ## YAML usage

    ```yaml
    >>> schedule:
    >>>   kind:
    >>>   startAt:
    >>>   endAt:
    >>>   maxRuns:
    >>>   frequency:
    >>>   dependsOnPast:
    ```

    ## Python usage

    ```python
    >>> from datetime import datetime, timedelta
    >>> from polyaxon.schemas import V1IntervalSchedule
    >>> schedule = V1IntervalSchedule(
    >>>   start_at=datetime(...),
    >>>   end_at=datetime(...),
    >>>   max_runs=20,
    >>>   frequency=timedelta(...),
    >>>   dependsOnPast=False,
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this schedule is an interval schedule.

    If you are using the python client to create the schedule,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: interval
    ```

    ### startAt

    Optional field to set the start time for kicking the first execution,
    all following executions will be relative to this time.

    ```yaml
    >>> run:
    >>>   startAt: "2019-06-24T21:20:07+00:00"
    ```

    ### endAt

    Optional field to set the end time for stopping this schedule.

    ```yaml
    >>> run:
    >>>   endAt: "2019-06-24T21:20:07+00:00"
    ```

    ### maxRuns

    The maximum number of times to execute the component.
    If used with end date, the schedule will terminate if one of the conditions is met.

    ```yaml
    >>> run:
    >>>   maxRuns: 10
    ```

    ### frequency

    The time delta value for setting the frequency of triggering executions.

    When using the python client you can pass `datetime.TimeDelta`
    where you can set human interpretable precision, e.g. `days`,
    and in the yaml specification you can only pass seconds.

    ```yaml
    >>> run:
    >>>   frequency: 120
    ```

    ### dependsOnPast

    Optional field to tell Polyaxon to check if the
    previous execution was done before scheduling a new one, by default this is set to `false`.

    ```yaml
    >>> run:
    >>>   dependsOnPast: true
    ```
    """

    _IDENTIFIER = V1ScheduleKind.INTERVAL
    _USE_DISCRIMINATOR = True

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    start_at: Optional[DatetimeOrRef] = Field(alias="startAt")
    end_at: Optional[DatetimeOrRef] = Field(alias="endAt")
    max_runs: Optional[IntOrRef] = Field(alias="maxRuns")
    frequency: TimeDeltaOrRef
    depends_on_past: Optional[BoolOrRef] = Field(alias="dependsOnPast")
