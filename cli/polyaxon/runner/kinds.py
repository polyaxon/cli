from clipped.utils.enums import PEnum


class RunnerKind(str, PEnum):
    K8S = "k8s"
    PROCESS = "process"
    DOCKER = "docker"
