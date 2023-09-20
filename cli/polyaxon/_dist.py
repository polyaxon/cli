from typing import Optional

LOCAL = "local"
SANDBOX = "sandbox"
CLOUD = "cloud"
CE = "ce"
EE = "ee"


def is_local(value: str):
    return LOCAL == value


def is_sandbox(value: str):
    return SANDBOX == value


def is_ce(value: str):
    return CE == value


def is_community(value: str):
    return value is None or value in {LOCAL, SANDBOX, CE}


def is_cloud(value: str):
    return CLOUD == value


def is_ee(value: str):
    return EE == value


def get_dist(value: str, default: Optional[str] = None):
    if value and value in {LOCAL, SANDBOX, CE, CLOUD, EE}:
        return value
    return default
