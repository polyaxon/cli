from polyaxon._flow import V1Notification
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.termination import V1Termination
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.pod.spec import get_pod_spec, get_pod_template_spec
from polyaxon._k8s.custom_resources.crd import get_custom_object
from polyaxon._k8s.custom_resources.service import get_service_custom_resource
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.schemas import V1Statuses


class TestServiceCRD(BaseTestCase):
    def test_get_service_custom_resource(self):
        main_container = k8s_schemas.V1Container(name="main")
        sidecar_containers = [k8s_schemas.V1Container(name="sidecar")]
        init_containers = [k8s_schemas.V1Container(name="init")]
        termination = V1Termination(timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "long-foo-bar" * 300},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
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
        custom_object = {
            "serviceSpec": {
                "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec),
            },
            "termination": {"activeDeadlineSeconds": termination.timeout},
            "collectLogs": True,
            "syncStatuses": True,
            "notifications": [],
        }
        expected_crd = get_custom_object(
            namespace="default",
            resource_name="foo",
            kind="Operation",
            api_version="core.polyaxon.com/v1",
            labels={"foo": "bar"},
            custom_object=custom_object,
            annotations={"foo": "long-foo-bar" * 300},
        )

        crd = get_service_custom_resource(
            namespace="default",
            resource_name="foo",
            main_container=main_container,
            sidecar_containers=sidecar_containers,
            init_containers=init_containers,
            volumes=[],
            termination=termination,
            environment=environment,
            labels=environment.labels,
            annotations={"foo": "long-foo-bar" * 300},
            collect_logs=True,
            sync_statuses=True,
            notifications=None,
            ports=[],
            is_external=False,
            replicas=None,
        )

        assert crd == expected_crd

    def test_get_service_custom_resource_missing_keys(self):
        main_container = k8s_schemas.V1Container(name="main")
        metadata, pod_spec = get_pod_spec(
            namespace="default",
            main_container=main_container,
            sidecar_containers=None,
            init_containers=None,
            resource_name="foo",
            volumes=[],
            environment=None,
            labels=None,
            annotations=None,
        )
        notifications = [V1Notification(connections=["test"], trigger=V1Statuses.DONE)]
        custom_object = {
            "template": get_pod_template_spec(metadata=metadata, pod_spec=pod_spec),
            "ports": [12, 121, 12],
            "isExternal": True,
            "replicas": 4,
        }
        expected_crd = get_custom_object(
            namespace="default",
            resource_name="foo",
            kind="Operation",
            api_version="core.polyaxon.com/v1",
            labels=None,
            annotations=None,
            custom_object={
                "serviceSpec": custom_object,
                "collectLogs": False,
                "syncStatuses": False,
                "notifications": [n.to_operator() for n in notifications],
            },
        )

        crd = get_service_custom_resource(
            namespace="default",
            resource_name="foo",
            main_container=main_container,
            sidecar_containers=None,
            init_containers=None,
            volumes=[],
            termination=None,
            collect_logs=None,
            sync_statuses=None,
            notifications=notifications,
            environment=None,
            labels=None,
            annotations=None,
            ports=[12, 121, 12],
            is_external=True,
            replicas=4,
        )

        assert crd == expected_crd
