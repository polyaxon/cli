from polyaxon._flow import V1Notification
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.termination import V1Termination
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.pod.spec import get_pod_spec, get_pod_template_spec
from polyaxon._k8s.custom_resources.crd import get_custom_object
from polyaxon._k8s.custom_resources.job import get_job_custom_resource
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.schemas import V1Statuses


class TestJobCRD(BaseTestCase):
    def test_get_job_custom_resource(self):
        main_container = k8s_schemas.V1Container(name="main")
        sidecar_containers = [k8s_schemas.V1Container(name="sidecar")]
        init_containers = [k8s_schemas.V1Container(name="init")]
        termination = V1Termination(max_retries=5, ttl=10, timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "long-foo-bar" * 300},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        notifications = [V1Notification(connections=["test"], trigger=V1Statuses.DONE)]
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
        custom_object = {
            "batchJobSpec": {
                "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec),
            },
            "termination": {
                "backoffLimit": termination.max_retries,
                "activeDeadlineSeconds": termination.timeout,
                "ttlSecondsAfterFinished": termination.ttl,
            },
            "collectLogs": True,
            "syncStatuses": True,
            "notifications": [n.to_operator() for n in notifications],
        }
        expected_crd = get_custom_object(
            namespace="default",
            resource_name="foo",
            kind="Job",
            api_version="polyaxon.com/v1",
            labels={"foo": "bar"},
            custom_object=custom_object,
            annotations={"foo": "long-foo-bar" * 300},
        )

        crd = get_job_custom_resource(
            namespace="default",
            resource_name="foo",
            main_container=main_container,
            sidecar_containers=sidecar_containers,
            init_containers=init_containers,
            volumes=[],
            termination=termination,
            environment=environment,
            collect_logs=True,
            sync_statuses=True,
            notifications=notifications,
            labels=environment.labels,
            annotations={"foo": "long-foo-bar" * 300},
        )

        assert crd == expected_crd
