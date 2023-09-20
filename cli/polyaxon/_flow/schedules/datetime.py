from typing_extensions import Literal

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import DatetimeOrRef

from polyaxon._flow.schedules.enums import V1ScheduleKind
from polyaxon._schemas.base import BaseSchemaModel


class V1DateTimeSchedule(BaseSchemaModel):
    """Date schedule is an interface to kick a component execution at a specific time.

    Args:
        kind: str, should be equal to `datetime`
        start_at: datetime, required

    ## YAML usage

    ```yaml
    >>> schedule:
    >>>   kind:
    >>>   startAt:
    ```

    ## Python usage

    ```python
    >>> from datetime import datetime
    >>> from polyaxon.schemas import V1DateTimeSchedule
    >>> schedule = V1DateTimeSchedule(
    >>>   start_at=datetime(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this schedule
    is a datetime schedule.

    If you are using the python client to create the schedule,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: datetime
    ```

    ### startAt

    Optional field to set the start time for kicking the first execution,
    all following executions will be relative to this time.

    ```yaml
    >>> run:
    >>>   startAt: "2019-06-24T21:20:07+00:00"
    ```
    """

    _IDENTIFIER = V1ScheduleKind.DATETIME
    _USE_DISCRIMINATOR = True

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    start_at: DatetimeOrRef = Field(alias="startAt")

    @property
    def max_runs(self):
        return 0

    @property
    def end_at(self):
        return None

    @property
    def depends_on_past(self):
        return True
