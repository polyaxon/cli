from enum import Enum


class PullPolicy(str, Enum):
    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"
