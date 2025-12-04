from polyaxon._flow import V1Notification
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.run.ray.autoscaler import V1RayAutoscalerOptions
from polyaxon._flow.termination import V1Culling, V1Termination
from polyaxon._k8s.custom_resources.crd import get_custom_object
from polyaxon._k8s.custom_resources.ray_cluster import (
    _get_autoscaler_options,
    get_ray_cluster_custom_resource,
)
from polyaxon.schemas import V1Statuses
from tests.test_k8s.test_custom_resources.base_distributed import (
    BaseDistributedCRDTestCase,
)


class TestRayClusterCRD(BaseDistributedCRDTestCase):
    def test_get_ray_cluster_custom_resource_with_no_workers(self):
        termination = V1Termination(max_retries=5, ttl=10, timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        custom_object = {
            "rayClusterSpec": {},
            "termination": {
                "backoffLimit": termination.max_retries,
                "activeDeadlineSeconds": termination.timeout,
                "ttlSecondsAfterFinished": termination.ttl,
            },
            "collectLogs": False,
            "syncStatuses": False,
            "notifications": [],
        }
        expected_crd = get_custom_object(
            namespace="default",
            resource_name="foo",
            kind="Cluster",
            api_version="polyaxon.com/v1",
            labels={"foo": "bar"},
            annotations={"foo": "long-foo-bar" * 300},
            custom_object=custom_object,
        )

        crd = get_ray_cluster_custom_resource(
            resource_name="foo",
            namespace="default",
            head=None,
            workers=None,
            termination=termination,
            collect_logs=False,
            sync_statuses=False,
            notifications=None,
            entrypoint=None,
            metadata=None,
            runtime_env=None,
            ray_version=None,
            labels=environment.labels,
            annotations={"foo": "long-foo-bar" * 300},
        )

        assert crd == expected_crd

    def test_get_ray_cluster_custom_resource(self):
        termination = V1Termination(max_retries=5, ttl=10, timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        notifications = [V1Notification(connections=["test"], trigger=V1Statuses.DONE)]
        head, head_replica_template = self.get_replica(
            environment, custom={"dashboard-host": "0.0.0.0"}
        )
        head_replica_template["rayStartParams"] = {"dashboard-host": "0.0.0.0"}
        head_replica_template["groupName"] = "head"
        worker, worker_replica_template = self.get_replica(environment)
        worker_replica_template["groupName"] = "worker1"
        template_spec = {
            "entrypoint": "foo",
            "metadata": {"foo": "bar"},
            "runtimeEnv": "foo",
            "rayVersion": "0.0.0",
            "head": head_replica_template,
            "workers": [worker_replica_template],
        }
        custom_object = {
            "rayClusterSpec": template_spec,
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
            kind="Cluster",
            api_version="polyaxon.com/v1",
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            custom_object=custom_object,
        )

        crd = get_ray_cluster_custom_resource(
            resource_name="foo",
            namespace="default",
            head=head,
            workers={"worker1": worker},
            termination=termination,
            collect_logs=True,
            sync_statuses=True,
            notifications=notifications,
            entrypoint="foo",
            metadata={"foo": "bar"},
            runtime_env="foo",
            ray_version="0.0.0",
            labels=environment.labels,
            annotations={"foo": "bar"},
        )

        assert crd == expected_crd

    def test_get_autoscaler_options_with_autoscaler_options(self):
        """Test that autoscaler options are passed through."""
        opts = V1RayAutoscalerOptions(
            upscaling_mode="Conservative",
            image_pull_policy="Always",
        )
        result = _get_autoscaler_options(opts)

        assert result is not None
        assert result["upscalingMode"] == "Conservative"
        assert result["imagePullPolicy"] == "Always"

    def test_get_autoscaler_options_returns_none_when_empty(self):
        """Test that None is returned when no autoscaler config is provided."""
        result = _get_autoscaler_options(None)
        assert result is None

    def test_get_ray_cluster_custom_resource_with_autoscaling(self):
        """Test creating a Ray cluster CRD with autoscaling enabled."""
        termination = V1Termination(
            max_retries=5,
            ttl=10,
            timeout=10,
            culling=V1Culling(timeout=3600),
        )
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        autoscaler_options = V1RayAutoscalerOptions(
            upscaling_mode="Default",
            image_pull_policy="IfNotPresent",
        )
        head, head_replica_template = self.get_replica(
            environment, custom={"dashboard-host": "0.0.0.0"}
        )
        head_replica_template["rayStartParams"] = {"dashboard-host": "0.0.0.0"}
        head_replica_template["groupName"] = "head"
        worker, worker_replica_template = self.get_replica(environment)
        worker_replica_template["groupName"] = "gpu-workers"

        template_spec = {
            "rayVersion": "2.9.0",
            "head": head_replica_template,
            "workers": [worker_replica_template],
            "enableInTreeAutoscaling": True,
            "autoscalerOptions": {
                "upscalingMode": "Default",
                "imagePullPolicy": "IfNotPresent",
            },
        }
        custom_object = {
            "rayClusterSpec": template_spec,
            "termination": {
                "backoffLimit": termination.max_retries,
                "activeDeadlineSeconds": termination.timeout,
                "ttlSecondsAfterFinished": termination.ttl,
                "culling": {"timeout": 3600},
            },
            "collectLogs": False,
            "syncStatuses": False,
            "notifications": [],
        }

        expected_crd = get_custom_object(
            namespace="default",
            resource_name="foo",
            kind="Cluster",
            api_version="polyaxon.com/v1",
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            custom_object=custom_object,
        )

        crd = get_ray_cluster_custom_resource(
            resource_name="foo",
            namespace="default",
            head=head,
            workers={"gpu-workers": worker},
            termination=termination,
            collect_logs=False,
            sync_statuses=False,
            notifications=None,
            entrypoint=None,
            metadata=None,
            runtime_env=None,
            ray_version="2.9.0",
            labels=environment.labels,
            annotations={"foo": "bar"},
            enable_in_tree_autoscaling=True,
            autoscaler_options=autoscaler_options,
        )

        assert crd == expected_crd
