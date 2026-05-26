import mock
import pytest

from polyaxon._flow.run.enums import V1RunKind
from polyaxon._k8s.custom_resources import operation
from polyaxon._k8s.executor.executor import Executor
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonAgentError


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

    def test_list_ops_uses_current_polyaxon_crds(self):
        k8s_manager = mock.MagicMock()
        k8s_manager.list_custom_objects.side_effect = lambda **kwargs: [
            {"plural": kwargs["plural"]}
        ]
        self.executor._manager = k8s_manager

        ops = self.executor.list_ops(namespace="runs")

        expected_resources = [
            (operation.GROUP, operation.API_VERSION, operation.JOB_PLURAL),
            (operation.GROUP, operation.API_VERSION, operation.SERVICES_PLURAL),
            (operation.GROUP, operation.API_VERSION, operation.KFJOB_PLURAL),
            (operation.GROUP, operation.API_VERSION, operation.CLUSTER_PLURAL),
        ]
        assert ops == [{"plural": resource[2]} for resource in expected_resources]
        called_resources = [
            (call[1]["group"], call[1]["version"], call[1]["plural"])
            for call in k8s_manager.list_custom_objects.call_args_list
        ]
        assert called_resources == expected_resources
        assert operation.PLURAL not in [resource[2] for resource in called_resources]
        assert all(
            call[1]["namespace"] == "runs"
            for call in k8s_manager.list_custom_objects.call_args_list
        )

    def test_start_apply_stop_get_raises_for_non_recognized_kinds(self):
        with self.assertRaises(PolyaxonAgentError):
            self.executor.create(run_uuid="", run_kind="foo", resource={})

        with self.assertRaises(PolyaxonAgentError):
            self.executor.apply(run_uuid="", run_kind="foo", resource={})

        with self.assertRaises(PolyaxonAgentError):
            self.executor.stop(run_uuid="", run_kind="foo")

        with self.assertRaises(PolyaxonAgentError):
            self.executor.get(run_uuid="", run_kind="foo")
