import pytest
import uuid

from mock import mock, MagicMock, patch

from polyaxon._client.run import RunClient
from polyaxon._schemas.lifecycle import V1Statuses, V1StatusCondition
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException
from traceml.artifacts import V1RunArtifact


@pytest.mark.client_mark
class TestRunClient(BaseTestCase):
    """Test suite for RunClient with mocked REST client to prevent connection pool leaks"""

    def setUp(self):
        super().setUp()
        self.owner = "test-owner"
        self.project = "test-project"
        self.run_uuid = uuid.uuid4().hex
        self.run_uuid_2 = uuid.uuid4().hex

        # Mock the REST client to prevent urllib3 connection pool creation
        self.rest_patcher = patch("polyaxon._sdk.sync_client.rest.RESTClientObject")
        self.mock_rest = self.rest_patcher.start()

    def tearDown(self):
        """Clean up mocks"""
        self.rest_patcher.stop()
        super().tearDown()

    # Initialization Tests
    def test_run_client_initialization(self):
        """Test RunClient initialization with owner, project, and run_uuid"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        assert client.owner == self.owner
        assert client.project == self.project
        assert client.run_uuid == self.run_uuid

    def test_run_client_without_project_raises(self):
        """Test initialization without project raises exception"""
        with pytest.raises(PolyaxonClientException):
            RunClient(owner=self.owner, run_uuid=self.run_uuid)

    # Basic Run Operations Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.get_run")
    def test_refresh_data(self, mock_get):
        """Test fetching run data from API"""
        mock_run = V1Run(
            uuid=self.run_uuid,
            name="test-run",
            description="Test run",
        )
        mock_get.return_value = mock_run

        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.refresh_data()

        assert mock_get.call_count == 1
        mock_get.assert_called_with(self.owner, self.project, self.run_uuid)
        assert client.run_data.name == "test-run"

    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run")
    def test_create_run(self, mock_create):
        """Test creating a new run (non-managed)"""
        mock_run = V1Run(
            uuid=self.run_uuid,
            name="new-run",
            description="A new run",
        )
        mock_create.return_value = mock_run

        client = RunClient(owner=self.owner, project=self.project)
        # Create a non-managed run (no content)
        result = client.create(name="new-run", description="A new run")

        assert mock_create.call_count == 1
        assert result.name == "new-run"

    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_update_run(self, mock_patch):
        """Test updating a run"""
        update_data = {"description": "Updated description"}
        mock_run = V1Run(
            uuid=self.run_uuid,
            description="Updated description",
        )
        mock_patch.return_value = mock_run

        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        result = client.update(update_data)

        assert mock_patch.call_count == 1
        assert result.description == "Updated description"

    @mock.patch("polyaxon._sdk.api.RunsV1Api.delete_run")
    def test_delete_run(self, mock_delete):
        """Test deleting a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.delete()

        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(self.owner, self.project, self.run_uuid)

    @mock.patch("polyaxon._sdk.api.RunsV1Api.transfer_run")
    def test_transfer_run(self, mock_transfer):
        """Test transferring a run to another project"""
        to_project = "destination-project"

        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.transfer(to_project)

        assert mock_transfer.call_count == 1
        call_args = mock_transfer.call_args
        assert call_args[1]["body"]["project"] == to_project

    # Metadata Operations Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_set_name(self, mock_patch):
        """Test setting run name"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.set_name("new-run-name")

        assert mock_patch.call_count == 1
        assert client.run_data.name == "new-run-name"

    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_set_description(self, mock_patch):
        """Test setting run description"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.set_description("New description")

        assert mock_patch.call_count == 1
        assert client.run_data.description == "New description"

    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_log_tags(self, mock_patch):
        """Test logging tags to a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        assert client.run_data.tags is None

        client.log_tags(["foo", "bar"])

        assert mock_patch.call_count == 1
        assert client.run_data.tags == ["foo", "bar"]

    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_log_tags_with_reset(self, mock_patch):
        """Test resetting tags on a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.run_data.tags = ["old-tag"]

        client.log_tags(["new-tag"], reset=True)

        assert client.run_data.tags == ["new-tag"]

    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_log_meta(self, mock_patch):
        """Test logging metadata to a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )

        client.log_meta(foo="bar", baz=123)

        assert mock_patch.call_count == 1
        assert client.run_data.meta_info["foo"] == "bar"
        assert client.run_data.meta_info["baz"] == 123

    # Inputs/Outputs Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_log_inputs(self, mock_patch):
        """Test logging inputs to a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )

        client.log_inputs(learning_rate=0.01, batch_size=32)

        assert mock_patch.call_count == 1
        assert client.run_data.inputs["learning_rate"] == 0.01
        assert client.run_data.inputs["batch_size"] == 32

    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_log_outputs(self, mock_patch):
        """Test logging outputs to a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )

        client.log_outputs(accuracy=0.95, loss=0.05)

        assert mock_patch.call_count == 1
        assert client.run_data.outputs["accuracy"] == 0.95
        assert client.run_data.outputs["loss"] == 0.05

    @mock.patch("polyaxon._sdk.api.RunsV1Api.get_run")
    def test_get_inputs(self, mock_get):
        """Test getting run inputs"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.run_data.inputs = {"learning_rate": 0.01, "batch_size": 32}

        inputs = client.get_inputs()

        assert inputs == {"learning_rate": 0.01, "batch_size": 32}
        # refresh_data should not be called since inputs are set
        assert mock_get.call_count == 0

    @mock.patch("polyaxon._sdk.api.RunsV1Api.get_run")
    def test_get_outputs(self, mock_get):
        """Test getting run outputs"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        # Set inputs to prevent refresh_data from being called
        client.run_data.inputs = {"some": "input"}
        client.run_data.outputs = {"accuracy": 0.95, "loss": 0.05}

        outputs = client.get_outputs()

        assert outputs == {"accuracy": 0.95, "loss": 0.05}
        # refresh_data should not be called since inputs are set
        assert mock_get.call_count == 0

    # Status Operations Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_status")
    def test_log_status(self, mock_create_status):
        """Test logging a status to a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )

        client.log_status(
            status=V1Statuses.RUNNING,
            reason="JobRunning",
            message="Run is in progress",
        )

        assert mock_create_status.call_count == 1
        call_args = mock_create_status.call_args
        # Access condition as an object attribute, not a dict
        assert call_args[1]["body"]["condition"].type == V1Statuses.RUNNING

    @mock.patch("polyaxon._sdk.api.RunsV1Api.get_run_statuses")
    def test_get_statuses(self, mock_get_statuses):
        """Test getting run statuses"""
        mock_condition = V1StatusCondition(
            type=V1Statuses.RUNNING,
            status=True,
            reason="JobRunning",
        )
        mock_response = MagicMock()
        mock_response.status = V1Statuses.RUNNING
        mock_response.status_conditions = [mock_condition]
        mock_get_statuses.return_value = mock_response

        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        status, conditions = client.get_statuses()

        assert mock_get_statuses.call_count == 1
        assert status == V1Statuses.RUNNING
        assert len(conditions) == 1
        assert conditions[0].type == V1Statuses.RUNNING

    @mock.patch("polyaxon._sdk.api.RunsV1Api.approve_run")
    def test_approve(self, mock_approve):
        """Test approving a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.approve()

        assert mock_approve.call_count == 1
        mock_approve.assert_called_with(self.owner, self.project, self.run_uuid)

    @mock.patch("polyaxon._sdk.api.RunsV1Api.skip_run")
    def test_skip(self, mock_skip):
        """Test skipping a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.skip()

        assert mock_skip.call_count == 1
        mock_skip.assert_called_with(self.owner, self.project, self.run_uuid)

    @mock.patch("polyaxon._sdk.api.RunsV1Api.invalidate_run")
    def test_invalidate(self, mock_invalidate):
        """Test invalidating a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.invalidate()

        assert mock_invalidate.call_count == 1
        mock_invalidate.assert_called_with(self.owner, self.project, self.run_uuid)

    @mock.patch("polyaxon._sdk.api.RunsV1Api.stop_run")
    def test_stop(self, mock_stop):
        """Test stopping a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.stop()

        assert mock_stop.call_count == 1
        mock_stop.assert_called_with(self.owner, self.project, self.run_uuid)

    # Lifecycle Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_status")
    def test_start(self, mock_create_status):
        """Test starting a run"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.start()

        assert mock_create_status.call_count == 1
        call_args = mock_create_status.call_args
        # Access condition as an object attribute
        assert call_args[1]["body"]["condition"].type == V1Statuses.RUNNING

    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_status")
    def test_log_succeeded(self, mock_create_status):
        """Test logging run as succeeded"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.log_succeeded()

        assert mock_create_status.call_count == 1
        call_args = mock_create_status.call_args
        # Access condition as an object attribute
        assert call_args[1]["body"]["condition"].type == V1Statuses.SUCCEEDED

    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_status")
    def test_log_stopped(self, mock_create_status):
        """Test logging run as stopped"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.log_stopped()

        assert mock_create_status.call_count == 1
        call_args = mock_create_status.call_args
        # Access condition as an object attribute
        assert call_args[1]["body"]["condition"].type == V1Statuses.STOPPED

    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_status")
    def test_log_failed(self, mock_create_status):
        """Test logging run as failed"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.log_failed(reason="Error", message="Something went wrong")

        assert mock_create_status.call_count == 1
        call_args = mock_create_status.call_args
        # Access condition as an object attribute
        assert call_args[1]["body"]["condition"].type == V1Statuses.FAILED
        assert call_args[1]["body"]["condition"].reason == "Error"

    # Artifact Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.get_run_artifacts_lineage")
    def test_get_artifacts_lineage(self, mock_get):
        """Test getting artifacts lineage for a run"""
        mock_artifact = V1RunArtifact(name="model.pkl", kind="model", path="models/")
        mock_response = MagicMock()
        mock_response.results = [mock_artifact]
        mock_get.return_value = mock_response

        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        result = client.get_artifacts_lineage()

        assert mock_get.call_count == 1
        assert len(result.results) == 1
        assert result.results[0].name == "model.pkl"

    # List Operations Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.list_runs")
    def test_list_runs(self, mock_list):
        """Test listing runs in a project"""
        mock_run = V1Run(uuid=self.run_uuid_2, name="test-run")
        mock_response = V1ListRunsResponse(results=[mock_run])
        mock_list.return_value = mock_response

        client = RunClient(owner=self.owner, project=self.project)
        result = client.list(query="status:running", limit=20)

        assert mock_list.call_count == 1
        mock_list.assert_called_with(
            self.owner, self.project, limit=20, query="status:running"
        )
        assert len(result.results) == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.list_runs")
    def test_list_children(self, mock_list):
        """Test listing children runs"""
        mock_run = V1Run(uuid=self.run_uuid_2, name="child-run")
        mock_response = V1ListRunsResponse(results=[mock_run])
        mock_list.return_value = mock_response

        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        result = client.list_children(limit=10)

        assert mock_list.call_count == 1
        call_args = mock_list.call_args
        # Should query for children of this run
        assert "pipeline" in call_args[1]["query"]

    # Code Reference Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_artifacts_lineage")
    def test_log_code_ref(self, mock_create_lineage):
        """Test logging code reference"""
        code_ref = {
            "commit": "abc123",
            "branch": "main",
            "url": "https://github.com/org/repo",
        }

        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.log_code_ref(code_ref)

        assert mock_create_lineage.call_count == 1

    # Data Reference Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_artifacts_lineage")
    def test_log_data_ref(self, mock_create_lineage):
        """Test logging data reference"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.log_data_ref(
            name="training-data",
            path="s3://bucket/data",
        )

        assert mock_create_lineage.call_count == 1

    # Model Reference Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.create_run_artifacts_lineage")
    def test_log_model_ref(self, mock_create_lineage):
        """Test logging model reference"""
        client = RunClient(
            owner=self.owner, project=self.project, run_uuid=self.run_uuid
        )
        client.log_model_ref(
            path="models/model.pkl",
            name="my-model",
            framework="pytorch",
        )

        assert mock_create_lineage.call_count == 1
