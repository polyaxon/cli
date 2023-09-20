from polyaxon._flow import V1Notification, V1SchedulingPolicy
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.termination import V1Termination
from polyaxon._k8s.custom_resources.crd import get_custom_object
from polyaxon._k8s.custom_resources.kubeflow import get_mpi_job_custom_resource
from polyaxon.schemas import V1Statuses
from tests.test_k8s.test_custom_resources.base_distributed import (
    BaseDistributedCRDTestCase,
)


class TestMPIJobCRD(BaseDistributedCRDTestCase):
    def test_get_mpi_job_custom_resource_with_no_workers(self):
        termination = V1Termination(max_retries=5, ttl=10, timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        custom_object = {
            "mpiJobSpec": {"cleanPodPolicy": "All", "replicaSpecs": {}},
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

        crd = get_mpi_job_custom_resource(
            namespace="default",
            resource_name="foo",
            launcher=None,
            worker=None,
            slots_per_worker=None,
            clean_pod_policy=None,
            scheduling_policy=None,
            termination=termination,
            collect_logs=False,
            sync_statuses=False,
            notifications=None,
            labels=environment.labels,
            annotations={"foo": "long-foo-bar" * 300},
        )

        assert crd == expected_crd

    def test_get_mpi_job_custom_resource(self):
        termination = V1Termination(max_retries=5, ttl=10, timeout=10)
        environment = V1Environment(
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            node_selector={"foo": "bar"},
            node_name="foo",
            restart_policy="Never",
        )
        notifications = [V1Notification(connections=["test"], trigger=V1Statuses.DONE)]
        launcher, launcher_replica_template = self.get_replica(environment)
        worker, worker_replica_template = self.get_replica(environment)
        template_spec = {
            "cleanPodPolicy": "Running",
            "schedulingPolicy": {"minAvailable": 1},
            "slotsPerWorker": 12,
            "replicaSpecs": {
                "Launcher": launcher_replica_template,
                "Worker": worker_replica_template,
            },
        }
        custom_object = {
            "mpiJobSpec": template_spec,
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

        crd = get_mpi_job_custom_resource(
            namespace="default",
            resource_name="foo",
            launcher=launcher,
            worker=worker,
            slots_per_worker=12,
            clean_pod_policy="Running",
            scheduling_policy=V1SchedulingPolicy(min_available=1),
            termination=termination,
            collect_logs=True,
            sync_statuses=True,
            notifications=notifications,
            labels=environment.labels,
            annotations={"foo": "bar"},
        )

        assert crd == expected_crd
