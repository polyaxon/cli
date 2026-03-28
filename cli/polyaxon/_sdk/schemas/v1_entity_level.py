from clipped.utils.enums import PEnum


class V1EntityLevel(str, PEnum):
    PROJECT_ENTITY = "entity"
    PROJECT = "project"
    CROSS_PROJECTS = "cross"
    ORG = "org"
