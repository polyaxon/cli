from clipped.utils.enums import PEnum

from polyaxon._schemas.lifecycle import V1Statuses


class V1TriggerPolicy(str, PEnum):
    ALL_SUCCEEDED = "all_succeeded"
    ALL_FAILED = "all_failed"
    ALL_DONE = "all_done"
    ONE_SUCCEEDED = "one_succeeded"
    ONE_FAILED = "one_failed"
    ONE_DONE = "one_done"

    @classmethod
    def trigger_statuses_mapping(cls):
        return {
            cls.ALL_SUCCEEDED: V1Statuses.SUCCEEDED,
            cls.ALL_FAILED: V1Statuses.FAILED,
            cls.ALL_DONE: V1Statuses.DONE,
            cls.ONE_SUCCEEDED: V1Statuses.SUCCEEDED,
            cls.ONE_FAILED: V1Statuses.FAILED,
            cls.ONE_DONE: V1Statuses.DONE,
        }
