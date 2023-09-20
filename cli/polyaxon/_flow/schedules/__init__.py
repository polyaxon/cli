from typing import Union
from typing_extensions import Annotated

from clipped.compact.pydantic import Field

from polyaxon._flow.schedules.cron import V1CronSchedule
from polyaxon._flow.schedules.datetime import V1DateTimeSchedule
from polyaxon._flow.schedules.enums import V1ScheduleKind
from polyaxon._flow.schedules.interval import V1IntervalSchedule

V1Schedule = Annotated[
    Union[V1IntervalSchedule, V1CronSchedule, V1DateTimeSchedule],
    Field(discriminator="kind"),
]


class ScheduleMixin:
    def get_schedule_kind(self):
        raise NotImplementedError

    @property
    def has_interval_schedule(self):
        return self.get_schedule_kind() == V1IntervalSchedule._IDENTIFIER

    @property
    def has_cron_schedule(self):
        return self.get_schedule_kind() == V1CronSchedule._IDENTIFIER

    @property
    def has_datetime_schedule(self):
        return self.get_schedule_kind() == V1DateTimeSchedule._IDENTIFIER
