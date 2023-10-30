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

    @classmethod
    def has_pipeline(cls, kind: str):
        return kind in (cls.DAG, cls.MATRIX, cls.SCHEDULE, cls.TUNER)

    @classmethod
    def has_service(cls, kind: str):
        return kind in (
            cls.SERVICE,
            cls.DASKJOB,
            cls.RAYJOB,
            cls.MPIJOB,
            cls.TFJOB,
            cls.PYTORCHJOB,
            cls.PADDLEJOB,
            cls.MXJOB,
            cls.XGBJOB,
        )


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
    MANUAL = "manual"


class V1RunPending(str, PEnum):
    APPROVAL = "approval"
    UPLOAD = "upload"
    CACHE = "cache"
    BUILD = "build"
