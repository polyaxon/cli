from clipped.utils.enums import PEnum


class ServiceTypes(str, PEnum):
    LOAD_BALANCER = "LoadBalancer"
    NODE_PORT = "NodePort"
    CLUSTER_IP = "ClusterIP"
