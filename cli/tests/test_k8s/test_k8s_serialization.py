import datetime
import pytest

from kubernetes import client as k8s_client

from polyaxon._flow.environment import V1Environment
from polyaxon._flow.termination import V1Termination
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.custom_resources.job import get_job_custom_resource
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon._vendor.k8s.serialization import sanitize_for_serialization


PYDANTIC_CLIENT = hasattr(k8s_client.V1EnvVar, "model_fields")


@pytest.mark.k8s_mark
class TestK8sSerialization(BaseTestCase):
    def test_serializes_models_with_api_keys(self):
        container = k8s_schemas.V1Container(
            name="main",
            image_pull_policy="Always",
            ports=[k8s_schemas.V1ContainerPort(container_port=8080)],
            env=[
                k8s_schemas.V1EnvVar(
                    name="FOO",
                    value_from=k8s_schemas.V1EnvVarSource(
                        secret_key_ref=k8s_schemas.V1SecretKeySelector(
                            name="secret", key="key"
                        )
                    ),
                )
            ],
            # Client models without a vendored version are passed through
            lifecycle=k8s_client.V1Lifecycle(
                pre_stop=k8s_client.V1LifecycleHandler(
                    sleep=k8s_client.V1SleepAction(seconds=5)
                )
            ),
        )
        resource = {
            "spec": {"containers": [container]},
            "args": ("a", 1),
            "created": datetime.date(2026, 1, 1),
        }

        assert sanitize_for_serialization(resource) == {
            "spec": {
                "containers": [
                    {
                        "name": "main",
                        "imagePullPolicy": "Always",
                        "ports": [{"containerPort": 8080}],
                        "env": [
                            {
                                "name": "FOO",
                                "valueFrom": {
                                    "secretKeyRef": {"name": "secret", "key": "key"}
                                },
                            }
                        ],
                        "lifecycle": {"preStop": {"sleep": {"seconds": 5}}},
                    }
                ]
            },
            "args": ("a", 1),
            "created": "2026-01-01",
        }

    @pytest.mark.skipif(PYDANTIC_CLIENT, reason="Only python-legacy client models")
    def test_matches_kubernetes_client(self):
        main_container = k8s_schemas.V1Container(
            name="main",
            image="foo:latest",
            args=["--epochs", "1"],
            resources=k8s_schemas.V1ResourceRequirements(
                requests={"cpu": "1"}, limits={"memory": "256Mi"}
            ),
            ports=[k8s_schemas.V1ContainerPort(container_port=8080, name="http")],
            env=[k8s_schemas.V1EnvVar(name="FOO", value="bar")],
            volume_mounts=[k8s_schemas.V1VolumeMount(name="data", mount_path="/data")],
            lifecycle=k8s_client.V1Lifecycle(
                pre_stop=k8s_client.V1LifecycleHandler(
                    sleep=k8s_client.V1SleepAction(seconds=5)
                )
            ),
        )
        environment = V1Environment(
            labels={"foo": "bar"},
            node_selector={"disk": "ssd"},
            restart_policy="Never",
        )
        crd = get_job_custom_resource(
            namespace="default",
            resource_name="foo",
            main_container=main_container,
            sidecar_containers=[k8s_schemas.V1Container(name="sidecar")],
            init_containers=[k8s_schemas.V1Container(name="init")],
            volumes=[
                k8s_schemas.V1Volume(
                    name="data", empty_dir=k8s_schemas.V1EmptyDirVolumeSource()
                )
            ],
            termination=V1Termination(max_retries=5, ttl=10, timeout=10),
            collect_logs=True,
            sync_statuses=True,
            notifications=[],
            environment=environment,
            labels=environment.labels,
            annotations={"foo": "bar"},
        )

        assert sanitize_for_serialization(
            crd
        ) == k8s_client.ApiClient().sanitize_for_serialization(crd)
