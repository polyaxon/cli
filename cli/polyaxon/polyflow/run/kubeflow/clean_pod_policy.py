from clipped.utils.enums import PEnum


class V1CleanPodPolicy(str, PEnum):
    ALL = "All"
    RUNNING = "Running"
    var_NONE = "None"
