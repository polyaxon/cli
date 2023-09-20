from polyaxon._constants.globals import UNKNOWN


class EventTypes:
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    ERROR = "ERROR"


class PodConditions:
    READY = "Ready"
    INITIALIZED = "Initialized"
    SCHEDULED = "PodScheduled"
    UNSCHEDULABLE = "Unschedulable"

    VALUES = [READY, INITIALIZED, SCHEDULED]


class PodLifeCycle:
    CONTAINER_CREATING = "ContainerCreating"
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = UNKNOWN

    DONE_STATUS = [FAILED, SUCCEEDED]
