from polyaxon._k8s.monitor import is_container_terminated
from polyaxon._utils.test_utils import BaseTestCase
from tests.test_k8s.fixtures import (
    status_run_job_event,
    status_run_job_event_with_conditions,
)


class TestK8sMonitor(BaseTestCase):
    def test_is_container_terminated_no_status(self):
        status = {"container_statuses": []}
        assert is_container_terminated(status, container_id="test") is None

        status = {"container_statuses": {}}
        assert is_container_terminated(status, container_id="test") is None

    def test_is_container_terminated(self):
        assert (
            is_container_terminated(
                status_run_job_event["object"]["status"], container_id="test"
            )
            is None
        )

        # using wrong container id
        assert (
            is_container_terminated(
                status_run_job_event_with_conditions["object"]["status"],
                container_id="test",
            )
            is None
        )

        # using correct container id
        assert (
            is_container_terminated(
                status_run_job_event_with_conditions["object"]["status"],
                container_id="polyaxon-main-job",
            )["exit_code"]
            == 1
        )
