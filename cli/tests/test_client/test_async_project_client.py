import inspect
from mock import mock
import os
import pytest
import tempfile
from unittest import IsolatedAsyncioTestCase

from polyaxon._client.project import AsyncProjectClient, ProjectClient
from polyaxon._contexts import paths as ctx_paths
from polyaxon._schemas.lifecycle import V1ProjectVersionKind, V1Stages
from polyaxon._sdk.schemas.v1_list_project_versions_response import (
    V1ListProjectVersionsResponse,
)
from polyaxon._sdk.schemas.v1_list_projects_response import V1ListProjectsResponse
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_project_version import V1ProjectVersion
from polyaxon._sdk.schemas.v1_uuids import V1Uuids
from polyaxon._utils.test_utils import AsyncMock, BaseTestCase
from polyaxon.exceptions import ApiException, PolyaxonClientException


OWNER = "test-owner"
TEAM = "test-team"
PROJECT = "test-project"
RUN_UUID1 = "11111111111111111111111111111111"
RUN_UUID2 = "22222222222222222222222222222222"

ASYNC_METHODS = {
    "refresh_data",
    "create",
    "get_or_create",
    "list",
    "delete",
    "update",
    "list_runs",
    "transfer_runs",
    "approve_runs",
    "archive_runs",
    "restore_runs",
    "delete_runs",
    "stop_runs",
    "skip_runs",
    "invalidate_runs",
    "bookmark_runs",
    "tag_runs",
    "list_versions",
    "list_component_versions",
    "list_model_versions",
    "list_artifact_versions",
    "get_version",
    "get_component_version",
    "get_model_version",
    "get_artifact_version",
    "get_version_stages",
    "get_component_version_stages",
    "get_model_version_stages",
    "get_artifact_version_stages",
    "create_version",
    "create_component_version",
    "create_model_version",
    "create_artifact_version",
    "patch_version",
    "patch_component_version",
    "patch_model_version",
    "patch_artifact_version",
    "register_version",
    "register_component_version",
    "register_model_version",
    "register_artifact_version",
    "delete_version",
    "delete_component_version",
    "delete_model_version",
    "delete_artifact_version",
    "stage_version",
    "stage_component_version",
    "stage_model_version",
    "stage_artifact_version",
    "transfer_version",
    "transfer_component_version",
    "transfer_model_version",
    "transfer_artifact_version",
    "copy_version",
    "copy_component_version",
    "copy_model_version",
    "copy_artifact_version",
    "persist_version",
    "download_artifacts_for_version",
    "pull_version",
    "pull_component_version",
    "pull_model_version",
    "pull_artifact_version",
    "load_offline_version",
    "push_version",
    "push_component_version",
    "push_model_version",
    "push_artifact_version",
}


class AsyncPolyaxonClientMock:
    is_async = True
    config = None

    def __init__(self):
        self.projects_v1 = mock.MagicMock()
        self.runs_v1 = mock.MagicMock()
        self.aclose_calls = 0

    async def aclose(self):
        self.aclose_calls += 1


class SyncPolyaxonClientMock:
    is_async = False
    config = None


@pytest.mark.client_mark
@pytest.mark.asyncio
class TestAsyncProjectClient(BaseTestCase, IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = mock.patch.object(
            ctx_paths,
            "CONTEXT_USER_POLYAXON_PATH",
            os.path.join(directory.name, ".polyaxon"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    def make_project_version(self, kind=V1ProjectVersionKind.MODEL, **kwargs):
        return V1ProjectVersion.model_construct(kind=kind, **kwargs)

    def test_async_project_client_public_export(self):
        from polyaxon.client import AsyncProjectClient as Exported

        assert Exported is AsyncProjectClient

    def test_async_project_client_rejects_sync_client(self):
        with self.assertRaises(PolyaxonClientException):
            AsyncProjectClient(
                owner=OWNER,
                project=PROJECT,
                client=SyncPolyaxonClientMock(),
            )

    def test_async_project_client_method_surface_is_async(self):
        for method in ASYNC_METHODS:
            assert method in AsyncProjectClient.__dict__
            assert inspect.iscoroutinefunction(getattr(AsyncProjectClient, method))

    def test_async_project_client_validate_kind_stays_local(self):
        assert AsyncProjectClient._validate_kind is ProjectClient._validate_kind
        assert not inspect.iscoroutinefunction(AsyncProjectClient._validate_kind)

    async def test_refresh_data_awaits_api_and_mutates_state(self):
        sdk_client = AsyncPolyaxonClientMock()
        response = V1Project.model_construct(name=PROJECT, owner=None)
        sdk_client.projects_v1.get_project = AsyncMock(return_value=response)
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        await client.refresh_data()

        sdk_client.projects_v1.get_project.assert_called_once_with(OWNER, PROJECT)
        assert client.project_data is response
        assert client.project_data.owner == OWNER

    async def test_refresh_data_returns_none_when_offline(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.projects_v1.get_project = AsyncMock()
        client = AsyncProjectClient(
            owner=OWNER,
            project=PROJECT,
            client=sdk_client,
            is_offline=True,
        )

        assert await client.refresh_data() is None
        assert sdk_client.projects_v1.get_project.call_count == 0

    async def test_create_project_awaits_organization_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        project_data = V1Project.model_construct(name="created-project")
        sdk_method = AsyncMock(return_value=project_data)
        sdk_client.projects_v1.create_project = sdk_method
        client = AsyncProjectClient(owner=OWNER, client=sdk_client)

        result = await client.create(project_data)

        assert result is project_data
        assert client.project == "created-project"
        sdk_method.assert_called_once_with(OWNER, project_data)
        assert "async_req" not in sdk_method.call_args[1]

    async def test_create_project_awaits_team_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        project_data = V1Project.model_construct(name="created-project")
        sdk_method = AsyncMock(return_value=project_data)
        sdk_client.projects_v1.create_team_project = sdk_method
        client = AsyncProjectClient(owner=f"{OWNER}/{TEAM}", client=sdk_client)

        result = await client.create(project_data)

        assert result is project_data
        assert client.project == "created-project"
        sdk_method.assert_called_once_with(OWNER, TEAM, project_data)
        assert "async_req" not in sdk_method.call_args[1]

    async def test_update_project_awaits_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        response = V1Project.model_construct(name=PROJECT)
        sdk_client.projects_v1.patch_project = AsyncMock(return_value=response)
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        result = await client.update({"description": "updated"})

        assert result is response
        sdk_client.projects_v1.patch_project.assert_called_once_with(
            OWNER, PROJECT, body={"description": "updated"}
        )
        assert "async_req" not in sdk_client.projects_v1.patch_project.call_args[1]

    async def test_project_list_delete_and_runs_await_api(self):
        sdk_client = AsyncPolyaxonClientMock()
        projects = V1ListProjectsResponse(results=[])
        runs = V1ListRunsResponse(results=[])
        sdk_client.projects_v1.list_projects = AsyncMock(return_value=projects)
        sdk_client.projects_v1.delete_project = AsyncMock(return_value=None)
        sdk_client.runs_v1.list_runs = AsyncMock(return_value=runs)
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        assert await client.list(limit=10, query="q") is projects
        assert await client.delete() is None
        assert await client.list_runs(limit=5, query="status:running") is runs

        sdk_client.projects_v1.list_projects.assert_called_once_with(
            OWNER, limit=10, query="q"
        )
        sdk_client.projects_v1.delete_project.assert_called_once_with(OWNER, PROJECT)
        sdk_client.runs_v1.list_runs.assert_called_once_with(
            OWNER, PROJECT, limit=5, query="status:running"
        )

    async def test_run_batch_methods_await_api(self):
        for method in (
            "approve_runs",
            "archive_runs",
            "restore_runs",
            "delete_runs",
            "stop_runs",
            "skip_runs",
            "invalidate_runs",
            "bookmark_runs",
        ):
            with self.subTest(method=method):
                sdk_client = AsyncPolyaxonClientMock()
                sdk_method = AsyncMock(return_value=None)
                setattr(sdk_client.runs_v1, method, sdk_method)
                client = AsyncProjectClient(
                    owner=OWNER, project=PROJECT, client=sdk_client
                )

                assert await getattr(client, method)([RUN_UUID1, RUN_UUID2]) is None

                sdk_method.assert_called_once()
                assert sdk_method.call_args[0] == (OWNER, PROJECT)
                payload = sdk_method.call_args[1]["body"]
                assert isinstance(payload, V1Uuids)
                assert payload.uuids == [RUN_UUID1, RUN_UUID2]

    async def test_transfer_and_tag_runs_await_api(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.runs_v1.transfer_runs = AsyncMock(return_value=None)
        sdk_client.runs_v1.tag_runs = AsyncMock(return_value=None)
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        assert await client.transfer_runs([RUN_UUID1], "target-project") is None
        assert await client.tag_runs([RUN_UUID1], ["tag1"]) is None

        transfer_body = sdk_client.runs_v1.transfer_runs.call_args[1]["body"]
        assert transfer_body.uuids == [RUN_UUID1]
        assert transfer_body.project == "target-project"
        tag_body = sdk_client.runs_v1.tag_runs.call_args[1]["body"]
        assert tag_body.uuids == [RUN_UUID1]
        assert tag_body.tags == ["tag1"]

    async def test_version_read_methods_await_api(self):
        sdk_client = AsyncPolyaxonClientMock()
        list_response = V1ListProjectVersionsResponse(results=[])
        version = self.make_project_version(name="v1")
        stages = mock.Mock(stage=V1Stages.PRODUCTION, stage_conditions=[])
        sdk_client.projects_v1.list_versions = AsyncMock(return_value=list_response)
        sdk_client.projects_v1.get_version = AsyncMock(return_value=version)
        sdk_client.projects_v1.get_version_stages = AsyncMock(return_value=stages)
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        assert (
            await client.list_versions(V1ProjectVersionKind.MODEL, limit=10)
            is list_response
        )
        assert await client.get_version(V1ProjectVersionKind.MODEL, "v1") is version
        assert await client.get_version_stages(V1ProjectVersionKind.MODEL, "v1") == (
            V1Stages.PRODUCTION,
            [],
        )

        sdk_client.projects_v1.list_versions.assert_called_once_with(
            OWNER, PROJECT, V1ProjectVersionKind.MODEL, limit=10
        )
        sdk_client.projects_v1.get_version.assert_called_once_with(
            OWNER, PROJECT, V1ProjectVersionKind.MODEL, "v1"
        )
        sdk_client.projects_v1.get_version_stages.assert_called_once_with(
            OWNER, PROJECT, V1ProjectVersionKind.MODEL, "v1"
        )

    async def test_get_version_rejects_kind_mismatch(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.projects_v1.get_version = AsyncMock(
            return_value=self.make_project_version(kind=V1ProjectVersionKind.COMPONENT)
        )
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        with self.assertRaises(PolyaxonClientException):
            await client.get_version(V1ProjectVersionKind.MODEL, "v1")

    async def test_create_version_awaits_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_method = AsyncMock(return_value=self.make_project_version(name="v1"))
        sdk_client.projects_v1.create_version = sdk_method
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        await client.create_version(V1ProjectVersionKind.MODEL, {"name": "v1"})

        assert sdk_method.call_count == 1
        assert "async_req" not in sdk_method.call_args[1]

    async def test_patch_version_awaits_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_method = AsyncMock(return_value=self.make_project_version(name="v1"))
        sdk_client.projects_v1.patch_version = sdk_method
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        await client.patch_version(
            V1ProjectVersionKind.MODEL, "v1", {"description": "updated"}
        )

        assert sdk_method.call_count == 1
        assert "async_req" not in sdk_method.call_args[1]

    async def test_delete_version_awaits_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_method = AsyncMock(return_value=self.make_project_version(name="v1"))
        sdk_client.projects_v1.delete_version = sdk_method
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        await client.delete_version(V1ProjectVersionKind.MODEL, "v1")

        assert sdk_method.call_count == 1
        assert "async_req" not in sdk_method.call_args[1]

    async def test_stage_version_awaits_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_method = AsyncMock(return_value=self.make_project_version(name="v1"))
        sdk_client.projects_v1.create_version_stage = sdk_method
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        await client.stage_version(V1ProjectVersionKind.MODEL, "v1", V1Stages.STAGING)

        assert sdk_method.call_count == 1
        assert "async_req" not in sdk_method.call_args[1]

    async def test_transfer_version_awaits_api_without_async_req(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_method = AsyncMock(return_value=self.make_project_version(name="v1"))
        sdk_client.projects_v1.transfer_version = sdk_method
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        await client.transfer_version(
            V1ProjectVersionKind.MODEL, "v1", "target-project"
        )

        assert sdk_method.call_count == 1
        assert "async_req" not in sdk_method.call_args[1]

    async def test_version_shortcuts_use_expected_kinds(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.projects_v1.list_versions = AsyncMock(
            return_value=V1ListProjectVersionsResponse(results=[])
        )
        sdk_client.projects_v1.create_version = AsyncMock(
            return_value=self.make_project_version(name="v1")
        )
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        await client.list_component_versions()
        await client.list_model_versions()
        await client.list_artifact_versions()
        await client.create_component_version({"name": "component"})

        list_calls = sdk_client.projects_v1.list_versions.call_args_list
        assert list_calls[0][0] == (OWNER, PROJECT, V1ProjectVersionKind.COMPONENT)
        assert list_calls[1][0] == (OWNER, PROJECT, V1ProjectVersionKind.MODEL)
        assert list_calls[2][0] == (OWNER, PROJECT, V1ProjectVersionKind.ARTIFACT)
        assert sdk_client.projects_v1.create_version.call_args[0] == (
            OWNER,
            PROJECT,
            V1ProjectVersionKind.COMPONENT,
        )

    async def test_register_version_create_and_update_paths(self):
        sdk_client = AsyncPolyaxonClientMock()
        created = self.make_project_version(name="v1")
        patched = self.make_project_version(name="v1")
        sdk_client.projects_v1.get_version = AsyncMock(
            side_effect=[
                ApiException(status=404, reason="missing"),
                self.make_project_version(name="v1"),
            ]
        )
        sdk_client.projects_v1.create_version = AsyncMock(return_value=created)
        sdk_client.projects_v1.patch_version = AsyncMock(return_value=patched)
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        assert (
            await client.register_version(
                kind=V1ProjectVersionKind.MODEL,
                version="v1",
                content={"a": 1},
            )
            is created
        )
        assert (
            await client.register_version(
                kind=V1ProjectVersionKind.MODEL,
                version="v1",
                force=True,
                description="updated",
            )
            is patched
        )

        assert sdk_client.projects_v1.create_version.call_count == 1
        assert sdk_client.projects_v1.patch_version.call_count == 1
        create_body = sdk_client.projects_v1.create_version.call_args[1]["body"]
        patch_body = sdk_client.projects_v1.patch_version.call_args[1]["body"]
        assert create_body.content == '{"a":1}'
        assert patch_body.description == "updated"

    async def test_register_version_existing_without_force_raises(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.projects_v1.get_version = AsyncMock(
            return_value=self.make_project_version(name="v1")
        )
        sdk_client.projects_v1.create_version = AsyncMock()
        sdk_client.projects_v1.patch_version = AsyncMock()
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        with self.assertRaises(PolyaxonClientException):
            await client.register_version(V1ProjectVersionKind.MODEL, "v1")

        assert sdk_client.projects_v1.create_version.call_count == 0
        assert sdk_client.projects_v1.patch_version.call_count == 0

    async def test_copy_version_uses_async_project_client_for_destination(self):
        sdk_client = AsyncPolyaxonClientMock()
        original = self.make_project_version(
            name="v1",
            description="source",
            tags=["tag1"],
            content='{"source":true}',
            run=RUN_UUID1,
        )
        copied = self.make_project_version(name="v1-copy")
        sdk_client.projects_v1.get_version = AsyncMock(
            side_effect=[
                original,
                ApiException(status=404, reason="missing"),
            ]
        )
        sdk_client.projects_v1.create_version = AsyncMock(return_value=copied)
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        assert (
            await client.copy_version(
                kind=V1ProjectVersionKind.MODEL,
                version="v1",
                to_project="target-project",
            )
            is copied
        )

        sdk_client.projects_v1.create_version.assert_called_once()
        assert sdk_client.projects_v1.create_version.call_args[0] == (
            OWNER,
            "target-project",
            V1ProjectVersionKind.MODEL,
        )
        body = sdk_client.projects_v1.create_version.call_args[1]["body"]
        assert body.name == "v1-copy"
        assert body.description == "source"
        assert body.tags == ["tag1"]

    async def test_file_io_methods_are_sync_only_on_async_project_client(self):
        sdk_client = AsyncPolyaxonClientMock()
        client = AsyncProjectClient(owner=OWNER, project=PROJECT, client=sdk_client)

        with self.assertRaises(PolyaxonClientException):
            await client.push_version(V1ProjectVersionKind.MODEL, "v1", "/tmp/version")

        with self.assertRaises(PolyaxonClientException):
            await client.pull_version(V1ProjectVersionKind.MODEL, "v1", "/tmp/version")

        with self.assertRaises(PolyaxonClientException):
            await client.persist_version(
                self.make_project_version(name="v1"), "/tmp/version"
            )

        with self.assertRaises(PolyaxonClientException):
            await AsyncProjectClient.load_offline_version(
                V1ProjectVersionKind.MODEL, "v1", "/tmp/version"
            )
