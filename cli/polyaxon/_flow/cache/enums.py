from clipped.utils.enums import PEnum


class CacheSection(str, PEnum):
    CONTAINERS = "containers"
    INIT = "init"
    CONNECTIONS = "connections"
