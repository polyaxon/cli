from typing import Union
from typing_extensions import Annotated

from clipped.compact.pydantic import Field

from polyaxon.polyflow.schedules.cron import V1CronSchedule
from polyaxon.polyflow.schedules.datetime import V1DateTimeSchedule
from polyaxon.polyflow.schedules.interval import V1IntervalSchedule
from polyaxon.polyflow.schedules.kinds import V1ScheduleKind

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
