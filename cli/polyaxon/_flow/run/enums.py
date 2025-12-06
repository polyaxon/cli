from clipped.utils.enums import PEnum


class V1RunKind(str, PEnum):
    JOB = "job"
    SERVICE = "service"
    DAG = "dag"
    DASKCLUSTER = "daskcluster"
    RAYCLUSTER = "raycluster"
    MPIJOB = "mpijob"
    TFJOB = "tfjob"
    PYTORCHJOB = "pytorchjob"
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
            cls.DASKCLUSTER,
            cls.RAYCLUSTER,
            cls.MPIJOB,
            cls.TFJOB,
            cls.PYTORCHJOB,
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
