from clipped.utils.enums import PEnum


class V1ScheduleKind(str, PEnum):
    CRON = "cron"
    INTERVAL = "interval"
    DATETIME = "datetime"
