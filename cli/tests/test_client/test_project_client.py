import pytest
import uuid

from mock import mock

from polyaxon._client.project import ProjectClient
from polyaxon._schemas.lifecycle import V1ProjectVersionKind, V1Stages
from polyaxon._sdk.schemas.v1_list_projects_response import V1ListProjectsResponse
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_list_project_versions_response import (
    V1ListProjectVersionsResponse,
)
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_project_version import V1ProjectVersion
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_uuids import V1Uuids
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


@pytest.mark.client_mark
class TestProjectClient(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = "test-owner"
        self.project = "test-project"
        self.team = "test-team"
        # Generate valid UUIDs for testing
        self.uuid1 = uuid.uuid4().hex
        self.uuid2 = uuid.uuid4().hex
        self.uuid3 = uuid.uuid4().hex
        self.run_uuid = uuid.uuid4().hex

    # Initialization Tests
    def test_project_client_initialization(self):
        """Test ProjectClient initialization with owner and project"""
        client = ProjectClient(owner=self.owner, project=self.project)
        assert client.owner == self.owner
        assert client.project == self.project
        assert client.team is None

    def test_project_client_with_team(self):
        """Test ProjectClient initialization with team scoping"""
        client = ProjectClient(owner=f"{self.owner}/{self.team}", project=self.project)
        assert client.owner == self.owner
        assert client.project == self.project
        assert client.team == self.team

    def test_project_client_without_owner_raises(self):
        """Test initialization without owner raises exception"""
        with pytest.raises(PolyaxonClientException):
            ProjectClient(owner=None, project=self.project)

    # Project Management Tests
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.get_project")
    def test_refresh_data(self, mock_get):
        """Test fetching project data from API"""
        mock_project = V1Project(
            name=self.project, owner=self.owner, description="Test project"
        )
        mock_get.return_value = mock_project

        client = ProjectClient(owner=self.owner, project=self.project)
        client.refresh_data()

        assert mock_get.call_count == 1
        assert client.project_data == mock_project

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.create_project")
    def test_create_project(self, mock_create):
        """Test creating a new project"""
        project_data = V1Project(name="new-project", description="A new project")
        mock_create.return_value = project_data

        client = ProjectClient(owner=self.owner)
        result = client.create(project_data)

        assert mock_create.call_count == 1
        assert result == project_data
        assert client.project == "new-project"

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.create_team_project")
    def test_create_project_with_team(self, mock_create):
        """Test creating a new project under a team"""
        project_data = V1Project(name="new-project", description="A team project")
        mock_create.return_value = project_data

        client = ProjectClient(owner=f"{self.owner}/{self.team}")
        result = client.create(project_data)

        assert mock_create.call_count == 1
        mock_create.assert_called_with(
            self.owner, self.team, project_data, async_req=False
        )
        assert result == project_data

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.list_projects")
    def test_list_projects(self, mock_list):
        """Test listing projects under the current owner"""
        mock_response = V1ListProjectsResponse(
            results=[
                V1Project(name="project1"),
                V1Project(name="project2"),
            ]
        )
        mock_list.return_value = mock_response

        client = ProjectClient(owner=self.owner)
        result = client.list(limit=10, query="status:active")

        assert mock_list.call_count == 1
        mock_list.assert_called_with(self.owner, limit=10, query="status:active")
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.delete_project")
    def test_delete_project(self, mock_delete):
        """Test deleting a project"""
        client = ProjectClient(owner=self.owner, project=self.project)
        client.delete()

        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(self.owner, self.project)

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.patch_project")
    def test_update_project(self, mock_patch):
        """Test updating a project"""
        update_data = {"description": "Updated description"}
        mock_project = V1Project(name=self.project, description="Updated description")
        mock_patch.return_value = mock_project

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.update(update_data)

        assert mock_patch.call_count == 1
        assert result == mock_project

    # Run Management Tests
    @mock.patch("polyaxon._sdk.api.RunsV1Api.list_runs")
    def test_list_runs(self, mock_list):
        """Test listing runs under the project"""
        mock_response = V1ListRunsResponse(results=[V1Run(uuid=self.run_uuid)])
        mock_list.return_value = mock_response

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.list_runs(query="status:running", limit=20)

        assert mock_list.call_count == 1
        mock_list.assert_called_with(
            self.owner, self.project, limit=20, query="status:running"
        )
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.RunsV1Api.transfer_runs")
    def test_transfer_runs_with_list(self, mock_transfer):
        """Test transferring runs with list of UUIDs"""
        uuids = [self.uuid1, self.uuid2]
        to_project = "destination-project"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.transfer_runs(uuids, to_project)

        assert mock_transfer.call_count == 1
        call_args = mock_transfer.call_args
        assert call_args[1]["body"].uuids == uuids
        assert call_args[1]["body"].project == to_project

    @mock.patch("polyaxon._sdk.api.RunsV1Api.transfer_runs")
    def test_transfer_runs_with_v1uuids(self, mock_transfer):
        """Test transferring runs with V1Uuids object"""
        uuids = V1Uuids(uuids=[self.uuid1, self.uuid2])
        to_project = "destination-project"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.transfer_runs(uuids, to_project)

        assert mock_transfer.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.approve_runs")
    def test_approve_runs(self, mock_approve):
        """Test batch approving runs"""
        uuids = [self.uuid1, self.uuid2]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.approve_runs(uuids)

        assert mock_approve.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.archive_runs")
    def test_archive_runs(self, mock_archive):
        """Test batch archiving runs"""
        uuids = V1Uuids(uuids=[self.uuid1, self.uuid2])

        client = ProjectClient(owner=self.owner, project=self.project)
        client.archive_runs(uuids)

        assert mock_archive.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.restore_runs")
    def test_restore_runs(self, mock_restore):
        """Test batch restoring runs"""
        uuids = [self.uuid1, self.uuid2]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.restore_runs(uuids)

        assert mock_restore.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.delete_runs")
    def test_delete_runs(self, mock_delete):
        """Test batch deleting runs"""
        uuids = [self.uuid1, self.uuid2, self.uuid3]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.delete_runs(uuids)

        assert mock_delete.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.stop_runs")
    def test_stop_runs(self, mock_stop):
        """Test batch stopping runs"""
        uuids = [self.uuid1, self.uuid2]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.stop_runs(uuids)

        assert mock_stop.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.skip_runs")
    def test_skip_runs(self, mock_skip):
        """Test batch skipping runs"""
        uuids = [self.uuid1, self.uuid2]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.skip_runs(uuids)

        assert mock_skip.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.invalidate_runs")
    def test_invalidate_runs(self, mock_invalidate):
        """Test batch invalidating runs"""
        uuids = [self.uuid1, self.uuid2]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.invalidate_runs(uuids)

        assert mock_invalidate.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.bookmark_runs")
    def test_bookmark_runs(self, mock_bookmark):
        """Test batch bookmarking runs"""
        uuids = [self.uuid1, self.uuid2]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.bookmark_runs(uuids)

        assert mock_bookmark.call_count == 1

    @mock.patch("polyaxon._sdk.api.RunsV1Api.tag_runs")
    def test_tag_runs(self, mock_tag):
        """Test batch tagging runs"""
        uuids = [self.uuid1, self.uuid2]
        tags = ["production", "validated"]

        client = ProjectClient(owner=self.owner, project=self.project)
        client.tag_runs(uuids, tags)

        assert mock_tag.call_count == 1
        call_args = mock_tag.call_args
        assert call_args[1]["body"].uuids == uuids
        assert call_args[1]["body"].tags == tags

    # Version Management Tests - Validation
    def test_validate_kind(self):
        """Test version kind validation"""
        client = ProjectClient(owner=self.owner, project=self.project)

        # Valid kinds should not raise
        client._validate_kind(V1ProjectVersionKind.MODEL)
        client._validate_kind(V1ProjectVersionKind.COMPONENT)
        client._validate_kind(V1ProjectVersionKind.ARTIFACT)

        # Invalid kind should raise
        with pytest.raises(ValueError):
            client._validate_kind("invalid_kind")

    # Version Management Tests - List
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.list_versions")
    def test_list_versions(self, mock_list):
        """Test listing versions by kind"""
        mock_response = V1ListProjectVersionsResponse(results=[])
        mock_list.return_value = mock_response

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.list_versions(
            kind=V1ProjectVersionKind.MODEL, query="stage:production", limit=20
        )

        assert mock_list.call_count == 1
        mock_list.assert_called_with(
            self.owner,
            self.project,
            V1ProjectVersionKind.MODEL,
            limit=20,
            query="stage:production",
        )
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.list_versions")
    def test_list_component_versions(self, mock_list):
        """Test listing component versions"""
        mock_response = V1ListProjectVersionsResponse(results=[])
        mock_list.return_value = mock_response

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.list_component_versions(limit=20)

        assert mock_list.call_count == 1
        call_args = mock_list.call_args
        assert call_args[0] == (
            self.owner,
            self.project,
            V1ProjectVersionKind.COMPONENT,
        )

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.list_versions")
    def test_list_model_versions(self, mock_list):
        """Test listing model versions"""
        client = ProjectClient(owner=self.owner, project=self.project)
        client.list_model_versions()

        assert mock_list.call_count == 1

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.list_versions")
    def test_list_artifact_versions(self, mock_list):
        """Test listing artifact versions"""
        client = ProjectClient(owner=self.owner, project=self.project)
        client.list_artifact_versions(limit=50)

        assert mock_list.call_count == 1

    # Version Management Tests - Get
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.get_version")
    def test_get_version(self, mock_get):
        """Test getting a specific version by kind and name"""
        version_name = "v1.0.0"
        mock_version = V1ProjectVersion(
            name=version_name, kind=V1ProjectVersionKind.MODEL
        )
        mock_get.return_value = mock_version

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.get_version(V1ProjectVersionKind.MODEL, version_name)

        assert mock_get.call_count == 1
        mock_get.assert_called_with(
            self.owner, self.project, V1ProjectVersionKind.MODEL, version_name
        )
        assert result == mock_version

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.get_version")
    def test_get_component_version(self, mock_get):
        """Test getting a component version"""
        version_name = "v1.0.0"
        mock_version = V1ProjectVersion(
            name=version_name, kind=V1ProjectVersionKind.COMPONENT
        )
        mock_get.return_value = mock_version

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.get_component_version(version_name)

        assert mock_get.call_count == 1
        assert result == mock_version

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.get_version")
    def test_get_model_version(self, mock_get):
        """Test getting a model version"""
        version_name = "v1.0.0"
        mock_version = V1ProjectVersion(
            name=version_name, kind=V1ProjectVersionKind.MODEL
        )
        mock_get.return_value = mock_version

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.get_model_version(version_name)

        assert mock_get.call_count == 1
        assert result == mock_version

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.get_version")
    def test_get_artifact_version(self, mock_get):
        """Test getting an artifact version"""
        version_name = "v1.0.0"
        mock_version = V1ProjectVersion(
            name=version_name, kind=V1ProjectVersionKind.ARTIFACT
        )
        mock_get.return_value = mock_version

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.get_artifact_version(version_name)

        assert mock_get.call_count == 1
        assert result == mock_version

    # Version Management Tests - Create
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.create_version")
    def test_create_version(self, mock_create):
        """Test creating a new version"""
        version_data = V1ProjectVersion(name="v1.0.0", description="Initial release")
        mock_create.return_value = version_data

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.create_version(V1ProjectVersionKind.MODEL, version_data)

        assert mock_create.call_count == 1
        assert result == version_data

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.create_version")
    def test_create_component_version(self, mock_create):
        """Test creating a component version"""
        version_data = V1ProjectVersion(name="v1.0.0")
        mock_create.return_value = version_data

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.create_component_version(version_data)

        assert mock_create.call_count == 1
        assert result == version_data

    # Version Management Tests - Update
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.patch_version")
    def test_patch_version(self, mock_patch):
        """Test updating a version"""
        version_name = "v1.0.0"
        update_data = {"description": "Updated description"}
        mock_version = V1ProjectVersion(
            name=version_name, description="Updated description"
        )
        mock_patch.return_value = mock_version

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.patch_version(
            V1ProjectVersionKind.MODEL, version_name, update_data
        )

        assert mock_patch.call_count == 1
        assert result == mock_version

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.patch_version")
    def test_patch_component_version(self, mock_patch):
        """Test updating a component version"""
        version_name = "v1.0.0"
        update_data = {"description": "Updated"}
        mock_version = V1ProjectVersion(name=version_name, description="Updated")
        mock_patch.return_value = mock_version

        client = ProjectClient(owner=self.owner, project=self.project)
        result = client.patch_component_version(version_name, update_data)

        assert mock_patch.call_count == 1
        assert result == mock_version

    # Version Management Tests - Delete
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.delete_version")
    def test_delete_version(self, mock_delete):
        """Test deleting a version"""
        version_name = "v1.0.0"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.delete_version(V1ProjectVersionKind.MODEL, version_name)

        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(
            self.owner,
            self.project,
            V1ProjectVersionKind.MODEL,
            version_name,
            async_req=False,
        )

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.delete_version")
    def test_delete_component_version(self, mock_delete):
        """Test deleting a component version"""
        version_name = "v1.0.0"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.delete_component_version(version_name)

        assert mock_delete.call_count == 1

    # Version Management Tests - Stage
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.create_version_stage")
    def test_stage_version(self, mock_stage):
        """Test staging a version"""
        version_name = "v1.0.0"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.stage_version(
            V1ProjectVersionKind.MODEL,
            version_name,
            V1Stages.PRODUCTION,
            reason="Deployment",
            message="Promoted to production",
        )

        assert mock_stage.call_count == 1
        call_args = mock_stage.call_args
        assert call_args[1]["body"]["condition"].type == V1Stages.PRODUCTION

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.create_version_stage")
    def test_stage_model_version(self, mock_stage):
        """Test staging a model version"""
        version_name = "v1.0.0"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.stage_model_version(version_name, V1Stages.STAGING)

        assert mock_stage.call_count == 1

    # Version Management Tests - Transfer
    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.transfer_version")
    def test_transfer_version(self, mock_transfer):
        """Test transferring a version to another project"""
        version_name = "v1.0.0"
        to_project = "destination-project"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.transfer_version(V1ProjectVersionKind.MODEL, version_name, to_project)

        assert mock_transfer.call_count == 1
        mock_transfer.assert_called_with(
            self.owner,
            self.project,
            V1ProjectVersionKind.MODEL,
            version_name,
            body={"project": to_project},
            async_req=False,
        )

    @mock.patch("polyaxon._sdk.api.ProjectsV1Api.transfer_version")
    def test_transfer_component_version(self, mock_transfer):
        """Test transferring a component version"""
        version_name = "v1.0.0"
        to_project = "destination-project"

        client = ProjectClient(owner=self.owner, project=self.project)
        client.transfer_component_version(version_name, to_project)

        assert mock_transfer.call_count == 1
