import pytest

from polyaxon._flow.environment import V1Environment
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.pod.spec import get_pod_spec
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonConverterError


@pytest.mark.converter_mark
class TestPodSpec(BaseTestCase):
    def test_get_pod_spec(self):
        init_container = k8s_schemas.V1Container(name="init")
        main_container = k8s_schemas.V1Container(name="main")
        sidecar_container = k8s_schemas.V1Container(name="sidecar")
        volumes = [k8s_schemas.V1Volume(name="vol")]
        labels = {"key": "labels"}
        annotations = {"key": "annotations"}
        node_selector = {"key": "selector"}
        affinity = {
            "podAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": [
                    {
                        "labelSelector": {
                            "matchExpressions": [
                                {"key": "app", "operator": "In", "values": ["nginx"]}
                            ]
                        },
                        "topologyKey": "kubernetes.io/hostname",
                    }
                ]
            }
        }

        tolerations = [
            {
                "key": "key1",
                "operator": "Equal",
                "value": "value1",
                "effect": "NoSchedule",
            },
            {
                "key": "key1",
                "operator": "Equal",
                "value": "value1",
                "effect": "NoExecute",
            },
        ]
        security_context = {
            "runAsUser": 1000,
            "runAsGroup": 3000,
        }
        restart_policy = "Never"

        with self.assertRaises(PolyaxonConverterError):
            get_pod_spec(
                namespace="default",
                main_container=None,
                sidecar_containers=None,
                init_containers=None,
                resource_name="foo",
                volumes=None,
                environment=V1Environment(),
                labels={},
                annotations={},
            )

        environment = V1Environment(
            service_account_name="sa",
            labels=labels,
            annotations=annotations,
            node_selector=node_selector,
            affinity=affinity,
            tolerations=tolerations,
            security_context=security_context,
            image_pull_secrets=[],
            restart_policy=restart_policy,
        )
        metadata, pod_spec = get_pod_spec(
            namespace="default",
            resource_name="foo",
            main_container=main_container,
            sidecar_containers=None,
            init_containers=None,
            volumes=None,
            environment=environment,
            labels=environment.labels,
            annotations=environment.annotations,
        )

        assert metadata.name == "foo"
        assert metadata.labels == labels
        assert metadata.namespace == "default"
        assert metadata.annotations == annotations

        assert isinstance(pod_spec, k8s_schemas.V1PodSpec)
        assert (
            V1Environment.swagger_to_dict(pod_spec.security_context) == security_context
        )
        assert pod_spec.restart_policy == "Never"
        assert pod_spec.service_account_name == "sa"
        assert pod_spec.init_containers == []
        assert pod_spec.containers == [main_container]
        assert pod_spec.volumes is None
        assert pod_spec.node_selector == node_selector
        assert [
            V1Environment.swagger_to_dict(t) for t in pod_spec.tolerations
        ] == tolerations
        assert V1Environment.swagger_to_dict(pod_spec.affinity) == affinity

        environment = V1Environment(
            service_account_name="sa",
            labels=labels,
            annotations=annotations,
            node_selector=node_selector,
            affinity=affinity,
            tolerations=tolerations,
            security_context=security_context,
            image_pull_secrets=[],
            restart_policy=restart_policy,
        )
        metadata, pod_spec = get_pod_spec(
            namespace="default",
            main_container=main_container,
            sidecar_containers=[sidecar_container],
            init_containers=[init_container],
            resource_name="foo",
            volumes=volumes,
            environment=environment,
            labels={},
            annotations={},
        )

        assert pod_spec.init_containers == [init_container]
        assert pod_spec.containers == [main_container, sidecar_container]
        assert pod_spec.volumes == volumes
        assert metadata.annotations == {}
