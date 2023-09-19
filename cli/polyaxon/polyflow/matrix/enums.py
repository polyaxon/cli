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


class AcquisitionFunctions(str, PEnum):
    UCB = "ucb"
    EI = "ei"
    POI = "poi"

    @classmethod
    def ucb_values(cls):
        return {cls.UCB, cls.UCB.upper(), cls.UCB.capitalize()}

    @classmethod
    def ei_values(cls):
        return {cls.EI, cls.EI.upper(), cls.EI.capitalize()}

    @classmethod
    def poi_values(cls):
        return {cls.POI, cls.POI.upper(), cls.POI.capitalize()}

    @classmethod
    def is_ucb(cls, value):
        return value in cls.ucb_values()

    @classmethod
    def is_ei(cls, value):
        return value in cls.ei_values()

    @classmethod
    def is_poi(cls, value):
        return value in cls.poi_values()


class GaussianProcessesKernels(str, PEnum):
    RBF = "rbf"
    MATERN = "matern"

    @classmethod
    def rbf_value(cls):
        return {cls.RBF, cls.RBF.upper(), cls.RBF.capitalize()}

    @classmethod
    def matern_value(cls):
        return {cls.MATERN, cls.MATERN.upper(), cls.MATERN.capitalize()}

    @classmethod
    def is_rbf(cls, value):
        return value in cls.rbf_value()

    @classmethod
    def is_mattern(cls, value):
        return value in cls.matern_value()
