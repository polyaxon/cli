from clipped.utils.enums import PEnum


class V1MatrixKind(str, PEnum):
    RANDOM = "random"
    GRID = "grid"
    HYPERBAND = "hyperband"
    BAYES = "bayes"
    HYPEROPT = "hyperopt"
    ITERATIVE = "iterative"
    MAPPING = "mapping"

    @classmethod
    def iteration_values(cls):
        return {
            cls.HYPERBAND,
            cls.BAYES,
            cls.HYPEROPT,
            cls.ITERATIVE,
        }


class V1HPKind(str, PEnum):
    CHOICE = "choice"
    PCHOICE = "pchoice"
    RANGE = "range"
    DATERANGE = "daterange"
    DATETIMERANGE = "datetimerange"
    LINSPACE = "linspace"
    LOGSPACE = "logspace"
    GEOMSPACE = "geomspace"
    UNIFORM = "uniform"
    QUNIFORM = "quniform"
    LOGUNIFORM = "loguniform"
    QLOGUNIFORM = "qloguniform"
    NORMAL = "normal"
    QNORMAL = "qnormal"
    LOGNORMAL = "lognormal"
    QLOGNORMAL = "qlognormal"
