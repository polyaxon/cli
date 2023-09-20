from clipped.utils.units import to_cpu_value, to_memory_bytes

from polyaxon._constants.globals import UNKNOWN


class NodeLifeCycle:
    UNKNOWN = UNKNOWN
    READY = "ready"
    NOT_READY = "notReady"
    DELETED = "deleted"

    CHOICES = (
        (UNKNOWN, UNKNOWN),
        (READY, READY),
        (NOT_READY, NOT_READY),
        (DELETED, DELETED),
    )


class NodeParser:
    @staticmethod
    def get_status(node) -> str:
        status = [c.status for c in node.status.conditions if c.type == "Ready"][0]
        if status == "True":
            return NodeLifeCycle.READY
        if status == "False":
            return NodeLifeCycle.NOT_READY
        return NodeLifeCycle.UNKNOWN

    @staticmethod
    def get_n_gpus(node) -> int:
        if "gpu" not in node.status.allocatable:
            return 0
        return int(node.status.allocatable.get("nvidia.com/gpu", 0))

    @staticmethod
    def get_cpu(node) -> float:
        cpu = node.status.allocatable["cpu"]
        return to_cpu_value(cpu)

    @classmethod
    def get_memory(cls, node) -> int:
        return to_memory_bytes(node.status.allocatable["memory"])

    @staticmethod
    def get_runtime(node) -> str:
        return node.status.node_info.container_runtime_version

    @staticmethod
    def get_schedulable_state(node) -> bool:
        return not node.spec.unschedulable

    @staticmethod
    def get_addresses(node) -> str:
        return node.status.addresses
