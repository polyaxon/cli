import inspect
from mock import mock
import pytest

from polyaxon._client.organization import AsyncOrganizationClient, OrganizationClient
from polyaxon._schemas.lifecycle import V1ProjectVersionKind
from polyaxon._sdk.schemas.v1_list_organization_members_response import (
    V1ListOrganizationMembersResponse,
)
from polyaxon._sdk.schemas.v1_list_organizations_response import (
    V1ListOrganizationsResponse,
)
from polyaxon._sdk.schemas.v1_list_project_versions_response import (
    V1ListProjectVersionsResponse,
)
from polyaxon._sdk.schemas.v1_list_run_artifacts_response import (
    V1ListRunArtifactsResponse,
)
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_organization import V1Organization
from polyaxon._sdk.schemas.v1_organization_member import V1OrganizationMember
from polyaxon._sdk.schemas.v1_uuids import V1Uuids
from polyaxon._utils.test_utils import AsyncMock, patch_settings
from polyaxon.exceptions import PolyaxonClientException


pytestmark = pytest.mark.client_mark

OWNER = "test-owner"
TEAM = "test-team"
RUN_UUID1 = "11111111111111111111111111111111"
RUN_UUID2 = "22222222222222222222222222222222"

ASYNC_METHODS = {
    "refresh_data",
    "list",
    "list_members",
    "get_member",
    "create_member",
    "update_member",
    "patch_member",
    "delete_member",
    "list_teams",
    "list_runs",
    "get_run",
    "approve_runs",
    "archive_runs",
    "restore_runs",
    "delete_runs",
    "stop_runs",
    "skip_runs",
    "invalidate_runs",
    "bookmark_runs",
    "tag_runs",
    "transfer_runs",
    "list_versions",
    "list_component_versions",
    "list_model_versions",
    "list_artifact_versions",
    "list_runs_artifacts_lineage",
}


class AsyncPolyaxonClientMock:
    is_async = True
    config = None

    def __init__(self):
        self.organizations_v1 = mock.MagicMock()
        self.teams_v1 = mock.MagicMock()
        self.aclose_calls = 0

    async def aclose(self):
        self.aclose_calls += 1


class SyncPolyaxonClientMock:
    is_async = False
    config = None


def test_async_organization_client_rejects_sync_client():
    patch_settings()

    with pytest.raises(PolyaxonClientException):
        AsyncOrganizationClient(owner=OWNER, client=SyncPolyaxonClientMock())


def test_async_organization_client_method_surface_is_async():
    for method in ASYNC_METHODS:
        assert inspect.iscoroutinefunction(getattr(AsyncOrganizationClient, method))
        assert getattr(AsyncOrganizationClient, method) is not getattr(
            OrganizationClient, method
        )


def test_async_organization_client_validate_kind_stays_local():
    assert AsyncOrganizationClient._validate_kind is OrganizationClient._validate_kind
    assert not inspect.iscoroutinefunction(AsyncOrganizationClient._validate_kind)


@pytest.mark.asyncio
async def test_async_organization_client_context_manager_smoke():
    patch_settings()
    client = AsyncOrganizationClient(owner=OWNER, client=AsyncPolyaxonClientMock())

    async with client as context_client:
        assert context_client is client


@pytest.mark.asyncio
async def test_refresh_data_awaits_api_and_mutates_state():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = V1Organization(name=None)
    sdk_client.organizations_v1.get_organization = AsyncMock(return_value=response)
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    await client.refresh_data()

    sdk_client.organizations_v1.get_organization.assert_called_once_with(OWNER)
    assert client.organization_data is response
    assert client.organization_data.name == OWNER


@pytest.mark.asyncio
async def test_refresh_data_returns_none_when_offline():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.organizations_v1.get_organization = AsyncMock()
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client, is_offline=True)

    assert await client.refresh_data() is None
    assert sdk_client.organizations_v1.get_organization.call_count == 0


@pytest.mark.asyncio
async def test_list_organizations_awaits_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = V1ListOrganizationsResponse(results=[])
    sdk_client.organizations_v1.list_organizations = AsyncMock(return_value=response)
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    result = await client.list(limit=10, offset=5, query="q", sort="-created_at")

    assert result is response
    sdk_client.organizations_v1.list_organizations.assert_called_once_with(
        limit=10, offset=5, query="q", sort="-created_at"
    )


@pytest.mark.asyncio
async def test_member_reads_await_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = V1ListOrganizationMembersResponse(results=[])
    sdk_client.organizations_v1.list_organization_members = AsyncMock(
        return_value=response
    )
    sdk_client.organizations_v1.get_organization_member = AsyncMock(
        return_value=V1OrganizationMember(user="user1")
    )
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    assert await client.list_members(limit=10) is response
    assert (await client.get_member("user1")).user == "user1"

    sdk_client.organizations_v1.list_organization_members.assert_called_once_with(
        OWNER, limit=10
    )
    sdk_client.organizations_v1.get_organization_member.assert_called_once_with(
        OWNER, "user1"
    )


@pytest.mark.asyncio
async def test_member_writes_do_not_pass_async_req():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    member = V1OrganizationMember(user="user1")
    sdk_client.organizations_v1.create_organization_member = AsyncMock(
        return_value=member
    )
    sdk_client.organizations_v1.update_organization_member = AsyncMock(
        return_value=member
    )
    sdk_client.organizations_v1.patch_organization_member = AsyncMock(
        return_value=member
    )
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    assert await client.create_member({"user": "user1"}, email="user@example.com")
    assert await client.update_member("user1", {"role": "admin"})
    assert await client.patch_member("user1", {"role": "member"})

    for call in (
        sdk_client.organizations_v1.create_organization_member.call_args,
        sdk_client.organizations_v1.update_organization_member.call_args,
        sdk_client.organizations_v1.patch_organization_member.call_args,
    ):
        assert "async_req" not in call[1]


@pytest.mark.asyncio
async def test_delete_member_awaits_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.organizations_v1.delete_organization_member = AsyncMock(
        return_value=None
    )
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    assert await client.delete_member("user1") is None
    sdk_client.organizations_v1.delete_organization_member.assert_called_once_with(
        OWNER, "user1"
    )


@pytest.mark.asyncio
async def test_list_teams_awaits_api_with_extra_params():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.teams_v1.list_teams = AsyncMock(return_value=mock.Mock())
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    await client.list_teams(limit=10, bookmarks=True, mode="stats")

    sdk_client.teams_v1.list_teams.assert_called_once_with(
        OWNER, limit=10, bookmarks=True, mode="stats"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "owner, api_group, method, expected_args",
    [
        (OWNER, "organizations_v1", "get_organization_runs", (OWNER,)),
        (
            f"{OWNER}/{TEAM}",
            "teams_v1",
            "get_team_runs",
            (OWNER, TEAM),
        ),
    ],
)
async def test_list_runs_awaits_correct_scope(owner, api_group, method, expected_args):
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = V1ListRunsResponse(results=[])
    sdk_method = AsyncMock(return_value=response)
    setattr(getattr(sdk_client, api_group), method, sdk_method)
    client = AsyncOrganizationClient(owner=owner, client=sdk_client)

    result = await client.list_runs(query="status:running", limit=10)

    assert result is response
    sdk_method.assert_called_once_with(*expected_args, limit=10, query="status:running")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "owner, api_group, method, expected_args",
    [
        (OWNER, "organizations_v1", "get_organization_run", (OWNER, "run-uuid")),
        (
            f"{OWNER}/{TEAM}",
            "teams_v1",
            "get_team_run",
            (OWNER, TEAM, "run-uuid"),
        ),
    ],
)
async def test_get_run_awaits_correct_scope(owner, api_group, method, expected_args):
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_method = AsyncMock(return_value=mock.Mock())
    setattr(getattr(sdk_client, api_group), method, sdk_method)
    client = AsyncOrganizationClient(owner=owner, client=sdk_client)

    await client.get_run("run-uuid")

    sdk_method.assert_called_once_with(*expected_args)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name, api_group, sdk_method_name, owner, expected_args, uses_body",
    [
        (
            "approve_runs",
            "organizations_v1",
            "approve_organization_runs",
            OWNER,
            (OWNER,),
            True,
        ),
        (
            "approve_runs",
            "teams_v1",
            "approve_team_runs",
            f"{OWNER}/{TEAM}",
            (OWNER, TEAM),
            False,
        ),
        (
            "delete_runs",
            "organizations_v1",
            "delete_organization_runs",
            OWNER,
            (OWNER,),
            True,
        ),
        (
            "delete_runs",
            "teams_v1",
            "delete_team_runs",
            f"{OWNER}/{TEAM}",
            (OWNER, TEAM),
            True,
        ),
    ],
)
async def test_run_batch_methods_await_correct_scope(
    method_name,
    api_group,
    sdk_method_name,
    owner,
    expected_args,
    uses_body,
):
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_method = AsyncMock(return_value=None)
    setattr(getattr(sdk_client, api_group), sdk_method_name, sdk_method)
    client = AsyncOrganizationClient(owner=owner, client=sdk_client)

    assert await getattr(client, method_name)([RUN_UUID1, RUN_UUID2]) is None

    sdk_method.assert_called_once()
    assert sdk_method.call_args[0][: len(expected_args)] == expected_args
    if uses_body:
        payload = sdk_method.call_args[1]["body"]
    else:
        payload = sdk_method.call_args[0][-1]
    assert isinstance(payload, V1Uuids)
    assert payload.uuids == [RUN_UUID1, RUN_UUID2]


@pytest.mark.asyncio
async def test_tag_runs_awaits_api_with_entities_tags():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.organizations_v1.tag_organization_runs = AsyncMock(return_value=None)
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    assert await client.tag_runs([RUN_UUID1], ["tag1"]) is None

    body = sdk_client.organizations_v1.tag_organization_runs.call_args[1]["body"]
    assert body.uuids == [RUN_UUID1]
    assert body.tags == ["tag1"]


@pytest.mark.asyncio
async def test_transfer_runs_awaits_api_with_entities_transfer():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.teams_v1.transfer_team_runs = AsyncMock(return_value=None)
    client = AsyncOrganizationClient(owner=f"{OWNER}/{TEAM}", client=sdk_client)

    assert await client.transfer_runs(V1Uuids(uuids=[RUN_UUID1]), "project-b") is None

    sdk_client.teams_v1.transfer_team_runs.assert_called_once()
    body = sdk_client.teams_v1.transfer_team_runs.call_args[1]["body"]
    assert body.uuids == [RUN_UUID1]
    assert body.project == "project-b"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "owner, api_group, method, expected_args",
    [
        (
            OWNER,
            "organizations_v1",
            "get_organization_versions",
            (OWNER, V1ProjectVersionKind.MODEL),
        ),
        (
            f"{OWNER}/{TEAM}",
            "teams_v1",
            "get_team_versions",
            (OWNER, TEAM, V1ProjectVersionKind.MODEL),
        ),
    ],
)
async def test_list_versions_awaits_correct_scope(
    owner, api_group, method, expected_args
):
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = V1ListProjectVersionsResponse(results=[])
    sdk_method = AsyncMock(return_value=response)
    setattr(getattr(sdk_client, api_group), method, sdk_method)
    client = AsyncOrganizationClient(owner=owner, client=sdk_client)

    result = await client.list_versions(
        kind=V1ProjectVersionKind.MODEL,
        query="stage:prod",
        limit=10,
    )

    assert result is response
    sdk_method.assert_called_once_with(
        *expected_args,
        limit=10,
        query="stage:prod",
    )


@pytest.mark.asyncio
async def test_list_versions_validates_kind_locally():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.organizations_v1.get_organization_versions = AsyncMock()
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    with pytest.raises(ValueError):
        await client.list_versions(kind="wrong")

    assert sdk_client.organizations_v1.get_organization_versions.call_count == 0


@pytest.mark.asyncio
async def test_version_shortcuts_await_list_versions():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.organizations_v1.get_organization_versions = AsyncMock(
        return_value=V1ListProjectVersionsResponse(results=[])
    )
    client = AsyncOrganizationClient(owner=OWNER, client=sdk_client)

    await client.list_component_versions(limit=1)
    await client.list_model_versions(limit=2)
    await client.list_artifact_versions(limit=3)

    calls = sdk_client.organizations_v1.get_organization_versions.call_args_list
    assert calls[0][0] == (OWNER, V1ProjectVersionKind.COMPONENT)
    assert calls[1][0] == (OWNER, V1ProjectVersionKind.MODEL)
    assert calls[2][0] == (OWNER, V1ProjectVersionKind.ARTIFACT)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "owner, api_group, method, expected_args",
    [
        (
            OWNER,
            "organizations_v1",
            "get_organization_runs_artifacts_lineage",
            (OWNER,),
        ),
        (
            f"{OWNER}/{TEAM}",
            "teams_v1",
            "get_team_runs_artifacts_lineage",
            (OWNER, TEAM),
        ),
    ],
)
async def test_list_runs_artifacts_lineage_awaits_correct_scope(
    owner, api_group, method, expected_args
):
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = V1ListRunArtifactsResponse(results=[])
    sdk_method = AsyncMock(return_value=response)
    setattr(getattr(sdk_client, api_group), method, sdk_method)
    client = AsyncOrganizationClient(owner=owner, client=sdk_client)

    result = await client.list_runs_artifacts_lineage(
        name="artifact",
        limit=10,
        bookmarks=True,
        mode="stats",
    )

    assert result is response
    sdk_method.assert_called_once_with(
        *expected_args,
        limit=10,
        name="artifact",
        bookmarks=True,
        mode="stats",
    )
