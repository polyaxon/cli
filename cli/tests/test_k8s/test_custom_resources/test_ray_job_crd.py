from polyaxon.k8s.custom_resources.crd import get_custom_object
from polyaxon.k8s.custom_resources.ray_job import get_ray_job_custom_resource
from polyaxon.lifecycle import V1Statuses
from polyaxon.polyflow import V1Notification
from polyaxon.polyflow.environment import V1Environment
from polyaxon.polyflow.termination import V1Termination
from tests.test_k8s.test_custom_resources.base_kubeflow import (
    BaseDistributedCRDTestCase,
)


class TestRayJobCRD(BaseDistributedCRDTestCase):
    def test_get_ray_job_custom_resource_with_no_workers(self):
        termination = V1Termination(max_retries=5, ttl=10, timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        custom_object = {
            "rayJobSpec": {},
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
            kind="Operation",
            api_version="core.polyaxon.com/v1",
            labels={"foo": "bar"},
            annotations={"foo": "long-foo-bar" * 300},
            custom_object=custom_object,
        )

        crd = get_ray_job_custom_resource(
            namespace="default",
            resource_name="foo",
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

    def test_get_ray_job_custom_resource(self):
        termination = V1Termination(max_retries=5, ttl=10, timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        notifications = [V1Notification(connections=["test"], trigger=V1Statuses.DONE)]
        head, head_replica_template = self.get_replica(environment)
        worker, worker_replica_template = self.get_replica(environment)
        template_spec = {
            "entrypoint": "foo",
            "metadata": {"foo": "bar"},
            "runtimeEnv": "foo",
            "rayVersion": "0.0.0",
            "head": head_replica_template,
            "workers": [worker_replica_template],
        }
        custom_object = {
            "rayJobSpec": template_spec,
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
            kind="Operation",
            api_version="core.polyaxon.com/v1",
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            custom_object=custom_object,
        )

        crd = get_ray_job_custom_resource(
            namespace="default",
            resource_name="foo",
            head=head,
            workers={"worker1": worker},
            entrypoint="foo",
            metadata={"foo": "bar"},
            runtime_env="foo",
            ray_version="0.0.0",
            termination=termination,
            collect_logs=True,
            sync_statuses=True,
            notifications=notifications,
            labels=environment.labels,
            annotations={"foo": "bar"},
        )

        assert crd == expected_crd
