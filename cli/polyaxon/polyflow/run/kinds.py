from clipped.utils.enums import PEnum


class V1RunKind(str, PEnum):
    JOB = "job"
    SERVICE = "service"
    DAG = "dag"
    DASKJOB = "daskjob"
    RAYJOB = "rayjob"
    MPIJOB = "mpijob"
    TFJOB = "tfjob"
    PYTORCHJOB = "pytorchjob"
    PADDLEJOB = "paddlejob"
    MXJOB = "mxjob"
    XGBJOB = "xgbjob"
    MATRIX = "matrix"
    SCHEDULE = "schedule"
    TUNER = "tuner"
    WATCHDOG = "watchdog"
    NOTIFIER = "notifier"
    CLEANER = "cleaner"
    BUILDER = "builder"


class V1CloningKind(str, PEnum):
    COPY = "copy"
    RESTART = "restart"
    CACHE = "cache"


class V1PipelineKind(str, PEnum):
    DAG = "dag"
    MATRIX = "matrix"


class V1RunEdgeKind(str, PEnum):
    ACTION = "action"
    EVENT = "event"
    HOOK = "hook"
    DAG = "dag"
    JOIN = "join"
    RUN = "run"
    TB = "tb"
    BUILD = "build"
