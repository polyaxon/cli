import mock
import pytest

from polyaxon.exceptions import PolyaxonAgentError
from polyaxon.k8s.executor.executor import Executor
from polyaxon.polyflow import V1RunKind
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.agent_mark
class TestExecutor(BaseTestCase):
    def setUp(self):
        self.executor = Executor()
        super().setUp()

    def test_start_apply_stop_get(self):
        k8s_manager = mock.MagicMock()
        k8s_manager.create_custom_object.return_value = ("", "")
        self.executor._manager = k8s_manager

        self.executor.create(run_uuid="", run_kind=V1RunKind.JOB, resource={})
        assert k8s_manager.create_custom_object.call_count == 1

        self.executor.apply(run_uuid="", run_kind=V1RunKind.JOB, resource={})
        assert k8s_manager.update_custom_object.call_count == 1

        self.executor.stop(run_uuid="", run_kind=V1RunKind.JOB)
        assert k8s_manager.delete_custom_object.call_count == 1

        self.executor.get(run_uuid="", run_kind=V1RunKind.JOB)
        assert k8s_manager.get_custom_object.call_count == 1

    def test_start_apply_stop_get_raises_for_non_recognized_kinds(self):
        with self.assertRaises(PolyaxonAgentError):
            self.executor.create(run_uuid="", run_kind="foo", resource={})

        with self.assertRaises(PolyaxonAgentError):
            self.executor.apply(run_uuid="", run_kind="foo", resource={})

        with self.assertRaises(PolyaxonAgentError):
            self.executor.stop(run_uuid="", run_kind="foo")

        with self.assertRaises(PolyaxonAgentError):
            self.executor.get(run_uuid="", run_kind="foo")
