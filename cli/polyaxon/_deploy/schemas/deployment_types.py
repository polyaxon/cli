from clipped.utils.enums import PEnum


class DeploymentTypes(str, PEnum):
    KUBERNETES = "kubernetes"
    MINIKUBE = "minikube"
    MICRO_K8S = "microk8s"
    DOCKER_COMPOSE = "docker-compose"
    DOCKER = "docker"
    HEROKU = "heroku"


class DeploymentCharts(str, PEnum):
    PLATFORM = "platform"
    AGENT = "agent"
    GATEWAY = "gateway"
