from collections import namedtuple


class ReplicaSpec(
    namedtuple(
        "ReplicaSpec",
        "volumes init_containers sidecar_containers main_container labels annotations environment num_replicas custom",
    )
):
    pass
