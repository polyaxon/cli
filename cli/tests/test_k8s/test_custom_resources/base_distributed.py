from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.pod.spec import get_pod_spec, get_pod_template_spec
from polyaxon._k8s.replica import ReplicaSpec
from polyaxon._utils.test_utils import BaseTestCase


class BaseDistributedCRDTestCase(BaseTestCase):
    def get_replica(self, environment, custom=None):
        main_container = k8s_schemas.V1Container(name="main")
        sidecar_containers = [k8s_schemas.V1Container(name="sidecar")]
        init_containers = [k8s_schemas.V1Container(name="init")]
        replica = ReplicaSpec(
            volumes=[],
            init_containers=init_containers,
            sidecar_containers=sidecar_containers,
            main_container=main_container,
            labels=environment.labels,
            annotations=environment.annotations,
            environment=environment,
            num_replicas=12,
            custom=custom,
        )
        metadata, pod_spec = get_pod_spec(
            namespace="default",
            main_container=main_container,
            sidecar_containers=sidecar_containers,
            init_containers=init_containers,
            resource_name="foo",
            volumes=[],
            environment=environment,
            labels=environment.labels,
            annotations=environment.annotations,
        )
        replica_template = {
            "replicas": replica.num_replicas,
            "restartPolicy": pod_spec.restart_policy,
            "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec),
        }
        return replica, replica_template
