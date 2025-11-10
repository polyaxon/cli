import pytest
import uuid

from mock import mock

from polyaxon._client.organization import OrganizationClient
from polyaxon._schemas.lifecycle import V1ProjectVersionKind
from polyaxon._sdk.schemas.v1_list_organizations_response import (
    V1ListOrganizationsResponse,
)
from polyaxon._sdk.schemas.v1_list_organization_members_response import (
    V1ListOrganizationMembersResponse,
)
from polyaxon._sdk.schemas.v1_list_project_versions_response import (
    V1ListProjectVersionsResponse,
)
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_list_teams_response import V1ListTeamsResponse
from polyaxon._sdk.schemas.v1_organization import V1Organization
from polyaxon._sdk.schemas.v1_organization_member import V1OrganizationMember
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_uuids import V1Uuids
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


@pytest.mark.client_mark
class TestOrganizationClient(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = "test-owner"
        self.team = "test-team"
        # Generate valid UUIDs for testing
        self.uuid1 = uuid.uuid4().hex
        self.uuid2 = uuid.uuid4().hex
        self.uuid3 = uuid.uuid4().hex
        self.run_uuid = uuid.uuid4().hex

    # Initialization Tests
    def test_organization_client_initialization(self):
        """Test OrganizationClient initialization with owner"""
        client = OrganizationClient(owner=self.owner)
        assert client.owner == self.owner
        assert client.team is None

    def test_organization_client_with_team(self):
        """Test OrganizationClient initialization with team scoping"""
        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        assert client.owner == self.owner
        assert client.team == self.team

    def test_organization_client_without_owner_raises(self):
        """Test initialization without owner raises exception"""
        with pytest.raises(PolyaxonClientException):
            OrganizationClient(owner=None)

    # Organization Management Tests
    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.list_organizations")
    def test_list_organizations(self, mock_list):
        """Test listing organizations"""
        mock_response = V1ListOrganizationsResponse(
            results=[V1Organization(name="org1"), V1Organization(name="org2")]
        )
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=self.owner)
        result = client.list(limit=10, offset=0)

        assert mock_list.call_count == 1
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.get_organization")
    def test_refresh_data(self, mock_get):
        """Test fetching organization data from API"""
        mock_org = V1Organization(name=self.owner, description="Test org")
        mock_get.return_value = mock_org

        client = OrganizationClient(owner=self.owner)
        client.refresh_data()

        assert mock_get.call_count == 1
        assert client.organization_data == mock_org

    # Member Management Tests
    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.list_organization_members")
    def test_list_members(self, mock_list):
        """Test listing organization members"""
        mock_response = V1ListOrganizationMembersResponse(
            results=[
                V1OrganizationMember(user="user1"),
                V1OrganizationMember(user="user2"),
            ]
        )
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=self.owner)
        result = client.list_members(limit=20)

        assert mock_list.call_count == 1
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.get_organization_member")
    def test_get_member(self, mock_get):
        """Test getting specific member details"""
        username = "test-user"
        mock_member = V1OrganizationMember(user=username, role="admin")
        mock_get.return_value = mock_member

        client = OrganizationClient(owner=self.owner)
        result = client.get_member(username)

        assert mock_get.call_count == 1
        assert result == mock_member

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.create_organization_member")
    def test_create_member(self, mock_create):
        """Test creating/inviting a new member"""
        member_data = {"user": "new-user", "role": "member"}
        mock_member = V1OrganizationMember(user="new-user", role="member")
        mock_create.return_value = mock_member

        client = OrganizationClient(owner=self.owner)
        result = client.create_member(member_data, email="new-user@example.com")

        assert mock_create.call_count == 1
        assert result == mock_member

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.delete_organization_member")
    def test_delete_member(self, mock_delete):
        """Test removing a member from organization"""
        username = "test-user"

        client = OrganizationClient(owner=self.owner)
        client.delete_member(username)

        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(self.owner, username)

    # Team Management Tests
    @mock.patch("polyaxon._sdk.api.TeamsV1Api.list_teams")
    def test_list_teams(self, mock_list):
        """Test listing teams in organization"""
        mock_response = V1ListTeamsResponse(
            results=[{"name": "team1"}, {"name": "team2"}]
        )
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=self.owner)
        result = client.list_teams(limit=20)

        assert mock_list.call_count == 1
        assert result == mock_response

    # Runs Management Tests - Organization Scope
    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.get_organization_runs")
    def test_list_runs_organization_scope(self, mock_list):
        """Test listing runs across all projects (no team)"""
        mock_response = V1ListRunsResponse(results=[V1Run(uuid=self.run_uuid)])
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=self.owner)
        result = client.list_runs(query="status:running", limit=20)

        assert mock_list.call_count == 1
        mock_list.assert_called_with(self.owner, limit=20, query="status:running")
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.TeamsV1Api.get_team_runs")
    def test_list_runs_team_scope(self, mock_list):
        """Test listing runs within team scope"""
        mock_response = V1ListRunsResponse(results=[V1Run(uuid=self.run_uuid)])
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        result = client.list_runs(limit=10)

        assert mock_list.call_count == 1
        mock_list.assert_called_with(self.owner, self.team, limit=10)
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.get_organization_run")
    def test_get_run_organization_scope(self, mock_get):
        """Test getting run by UUID (organization scope)"""
        mock_run = V1Run(uuid=self.run_uuid)
        mock_get.return_value = mock_run

        client = OrganizationClient(owner=self.owner)
        result = client.get_run(self.run_uuid)

        assert mock_get.call_count == 1
        assert result == mock_run

    @mock.patch("polyaxon._sdk.api.TeamsV1Api.get_team_run")
    def test_get_run_team_scope(self, mock_get):
        """Test getting run by UUID (team scope)"""
        mock_run = V1Run(uuid=self.run_uuid)
        mock_get.return_value = mock_run

        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        result = client.get_run(self.run_uuid)

        assert mock_get.call_count == 1
        mock_get.assert_called_with(self.owner, self.team, self.run_uuid)
        assert result == mock_run

    # Batch Run Operations Tests
    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.delete_organization_runs")
    def test_delete_runs_with_list(self, mock_delete):
        """Test batch deleting runs with list of UUIDs"""
        uuids = [self.uuid1, self.uuid2, self.uuid3]

        client = OrganizationClient(owner=self.owner)
        client.delete_runs(uuids)

        assert mock_delete.call_count == 1
        call_args = mock_delete.call_args
        assert isinstance(call_args[1]["body"], V1Uuids)
        assert call_args[1]["body"].uuids == uuids

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.delete_organization_runs")
    def test_delete_runs_with_v1uuids(self, mock_delete):
        """Test batch deleting runs with V1Uuids object"""
        uuids = V1Uuids(uuids=[self.uuid1, self.uuid2])

        client = OrganizationClient(owner=self.owner)
        client.delete_runs(uuids)

        assert mock_delete.call_count == 1

    @mock.patch("polyaxon._sdk.api.TeamsV1Api.delete_team_runs")
    def test_delete_runs_team_scope(self, mock_delete):
        """Test batch deleting runs (team scope)"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        client.delete_runs(uuids)

        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(self.owner, self.team, body=mock.ANY)

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.stop_organization_runs")
    def test_stop_runs_organization_scope(self, mock_stop):
        """Test batch stopping runs (organization scope)"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=self.owner)
        client.stop_runs(uuids)

        assert mock_stop.call_count == 1

    @mock.patch("polyaxon._sdk.api.TeamsV1Api.stop_team_runs")
    def test_stop_runs_team_scope(self, mock_stop):
        """Test batch stopping runs (team scope)"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        client.stop_runs(uuids)

        assert mock_stop.call_count == 1

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.approve_organization_runs")
    def test_approve_runs(self, mock_approve):
        """Test batch approving runs"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=self.owner)
        client.approve_runs(uuids)

        assert mock_approve.call_count == 1

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.archive_organization_runs")
    def test_archive_runs(self, mock_archive):
        """Test batch archiving runs"""
        uuids = V1Uuids(uuids=[self.uuid1, self.uuid2])

        client = OrganizationClient(owner=self.owner)
        client.archive_runs(uuids)

        assert mock_archive.call_count == 1

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.restore_organization_runs")
    def test_restore_runs(self, mock_restore):
        """Test batch restoring runs"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=self.owner)
        client.restore_runs(uuids)

        assert mock_restore.call_count == 1

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.invalidate_organization_runs")
    def test_invalidate_runs_organization_scope(self, mock_invalidate):
        """Test batch invalidating runs (organization scope)"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=self.owner)
        client.invalidate_runs(uuids)

        assert mock_invalidate.call_count == 1

    @mock.patch("polyaxon._sdk.api.TeamsV1Api.invalidate_team_runs")
    def test_invalidate_runs_team_scope(self, mock_invalidate):
        """Test batch invalidating runs (team scope)"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        client.invalidate_runs(uuids)

        assert mock_invalidate.call_count == 1

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.bookmark_organization_runs")
    def test_bookmark_runs(self, mock_bookmark):
        """Test batch bookmarking runs"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=self.owner)
        client.bookmark_runs(uuids)

        assert mock_bookmark.call_count == 1

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.skip_organization_runs")
    def test_skip_runs(self, mock_skip):
        """Test batch skipping runs"""
        uuids = [self.uuid1, self.uuid2]

        client = OrganizationClient(owner=self.owner)
        client.skip_runs(uuids)

        assert mock_skip.call_count == 1

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.tag_organization_runs")
    def test_tag_runs(self, mock_tag):
        """Test batch tagging runs"""
        data = {"uuids": [self.uuid1, self.uuid2], "tags": ["production", "validated"]}

        client = OrganizationClient(owner=self.owner)
        client.tag_runs(data)

        assert mock_tag.call_count == 1
        mock_tag.assert_called_with(self.owner, body=data)

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.transfer_organization_runs")
    def test_transfer_runs(self, mock_transfer):
        """Test transferring runs to different project"""
        data = {"uuids": [self.uuid1, self.uuid2], "project": "destination-project"}

        client = OrganizationClient(owner=self.owner)
        client.transfer_runs(data)

        assert mock_transfer.call_count == 1
        mock_transfer.assert_called_with(self.owner, body=data)

    # Version Management Tests
    def test_validate_kind(self):
        """Test version kind validation"""
        client = OrganizationClient(owner=self.owner)

        # Valid kinds should not raise
        client._validate_kind(V1ProjectVersionKind.MODEL)
        client._validate_kind(V1ProjectVersionKind.COMPONENT)
        client._validate_kind(V1ProjectVersionKind.ARTIFACT)

        # Invalid kind should raise
        with pytest.raises(ValueError):
            client._validate_kind("invalid_kind")

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.get_organization_versions")
    def test_list_versions_organization_scope(self, mock_list):
        """Test listing versions across all projects"""
        mock_response = V1ListProjectVersionsResponse(results=[])
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=self.owner)
        result = client.list_versions(
            kind=V1ProjectVersionKind.MODEL, query="stage:production", limit=20
        )

        assert mock_list.call_count == 1
        mock_list.assert_called_with(
            self.owner,
            V1ProjectVersionKind.MODEL,
            limit=20,
            query="stage:production",
        )
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.TeamsV1Api.get_team_versions")
    def test_list_versions_team_scope(self, mock_list):
        """Test listing versions within team scope"""
        mock_response = V1ListProjectVersionsResponse(results=[])
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        result = client.list_versions(
            kind=V1ProjectVersionKind.MODEL, limit=10, no_page=True
        )

        assert mock_list.call_count == 1
        mock_list.assert_called_with(
            self.owner,
            self.team,
            V1ProjectVersionKind.MODEL,
            limit=10,
            no_page=True,
        )
        assert result == mock_response

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.get_organization_versions")
    def test_list_component_versions(self, mock_list):
        """Test listing component versions convenience method"""
        mock_response = V1ListProjectVersionsResponse(results=[])
        mock_list.return_value = mock_response

        client = OrganizationClient(owner=self.owner)
        result = client.list_component_versions(limit=20)

        assert mock_list.call_count == 1
        call_args = mock_list.call_args
        assert call_args[0] == (self.owner, V1ProjectVersionKind.COMPONENT)

    @mock.patch("polyaxon._sdk.api.OrganizationsV1Api.get_organization_versions")
    def test_list_model_versions(self, mock_list):
        """Test listing model versions convenience method"""
        client = OrganizationClient(owner=self.owner)
        client.list_model_versions()

        assert mock_list.call_count == 1

    @mock.patch("polyaxon._sdk.api.TeamsV1Api.get_team_versions")
    def test_list_artifact_versions_team_scope(self, mock_list):
        """Test listing artifact versions (team scope)"""
        client = OrganizationClient(owner=f"{self.owner}/{self.team}")
        client.list_artifact_versions(limit=50)

        assert mock_list.call_count == 1
        call_args = mock_list.call_args
        assert call_args[0] == (self.owner, self.team, V1ProjectVersionKind.ARTIFACT)
