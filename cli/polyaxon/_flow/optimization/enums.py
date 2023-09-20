from clipped.utils.enums import PEnum


class V1ResourceType(str, PEnum):
    INT = "int"
    FLOAT = "float"

    @classmethod
    def init_values(cls):
        return {cls.INT, cls.INT.upper(), cls.INT.capitalize()}

    @classmethod
    def float_values(cls):
        return {cls.FLOAT, cls.FLOAT.upper(), cls.FLOAT.capitalize()}

    @classmethod
    def values(cls):
        return cls.init_values() | cls.float_values()

    @classmethod
    def is_int(cls, value):
        return value in cls.init_values()

    @classmethod
    def is_float(cls, value):
        return value in cls.float_values()


class V1Optimization(str, PEnum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"

    @classmethod
    def maximize_values(cls):
        return [cls.MAXIMIZE, cls.MAXIMIZE.upper(), cls.MAXIMIZE.capitalize()]

    @classmethod
    def minimize_values(cls):
        return [cls.MINIMIZE, cls.MINIMIZE.upper(), cls.MINIMIZE.capitalize()]

    @classmethod
    def maximize(cls, value):
        return value in cls.maximize_values()

    @classmethod
    def minimize(cls, value):
        return value in cls.minimize_values()
