import inspect
from mock import mock
import pytest

from clipped.utils.hashing import hash_file, hash_value
from polyaxon import settings
from polyaxon._client.run import AsyncRunClient, RunClient
from polyaxon._schemas.lifecycle import (
    V1ProjectVersionKind,
    V1StatusCondition,
    V1Statuses,
)
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_project_version import V1ProjectVersion
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_run_settings import V1RunSettings
from polyaxon._utils.test_utils import AsyncMock, patch_settings
from polyaxon.exceptions import ApiException, PolyaxonClientException
from traceml.artifacts import V1ArtifactKind, V1RunArtifact
from traceml.events import V1Events


pytestmark = pytest.mark.client_mark

OWNER = "test-owner"
PROJECT = "test-project"
RUN_UUID = "11111111111111111111111111111111"

ASYNC_METHODS = {
    "get_inputs",
    "get_outputs",
    "refresh_data",
    "update",
    "transfer",
    "create",
    "create_from_polyaxonfile",
    "create_from_url",
    "create_from_hub",
    "log_status",
    "get_statuses",
    "wait_for_condition",
    "watch_statuses",
    "get_logs",
    "watch_logs",
    "inspect",
    "shell",
    "get_events",
    "get_multi_run_events",
    "get_metrics",
    "get_metrics_as_tidy_df",
    "get_metrics_as_wide_df",
    "get_metrics_as_bar_chart",
    "get_metrics_as_line_chart",
    "get_metrics_as_scatter_chart",
    "get_runs_io",
    "get_runs_as_hiplot",
    "get_artifacts_lineage",
    "get_runs_artifacts_lineage",
    "get_artifact",
    "download_artifact_for_lineage",
    "download_artifact",
    "download_artifacts",
    "upload_artifact",
    "upload_artifacts_dir",
    "upload_artifacts",
    "delete_artifact",
    "delete_artifacts",
    "get_artifacts_tree",
    "stop",
    "skip",
    "approve",
    "invalidate",
    "restart",
    "resume",
    "set_readme",
    "set_description",
    "set_name",
    "log_inputs",
    "log_outputs",
    "log_meta",
    "log_tags",
    "start",
    "end",
    "log_succeeded",
    "log_stopped",
    "log_failed",
    "log_progress",
    "log_code_ref",
    "log_data_ref",
    "log_artifact_ref",
    "log_model_ref",
    "log_file_ref",
    "log_dir_ref",
    "log_tensorboard_ref",
    "log_artifact_lineage",
    "get_namespace",
    "delete",
    "list",
    "list_children",
    "promote_to_model_version",
    "set_run_edges_lineage",
    "promote_to_artifact_version",
    "sync_events_summaries",
    "sync_system_events_summaries",
    "persist_run",
    "load_offline_run",
    "pull_remote_run",
    "push_offline_run",
}


class AsyncPolyaxonClientMock:
    is_async = True
    config = None

    def __init__(self):
        self.runs_v1 = mock.MagicMock()
        self.organizations_v1 = mock.MagicMock()
        self.agents_v1 = mock.MagicMock()
        self.aclose_calls = 0

    async def aclose(self):
        self.aclose_calls += 1


class SyncPolyaxonClientMock:
    is_async = False
    config = None


def make_client(sdk_client):
    return AsyncRunClient(
        owner=OWNER,
        project=PROJECT,
        run_uuid=RUN_UUID,
        client=sdk_client,
    )


def make_run(**kwargs):
    data = {
        "owner": OWNER,
        "project": PROJECT,
        "uuid": RUN_UUID,
        "settings": V1RunSettings.model_construct(namespace="test-namespace"),
    }
    data.update(kwargs)
    return V1Run.model_construct(**data)


def get_logged_lineage_artifact(sdk_client, index=0):
    body = sdk_client.runs_v1.create_run_artifacts_lineage.call_args_list[index][1][
        "body"
    ]
    return body.artifacts[0]


def test_async_run_client_public_export():
    from polyaxon.client import AsyncRunClient as Exported

    assert Exported is AsyncRunClient


def test_async_run_client_rejects_sync_client():
    patch_settings()

    with pytest.raises(PolyaxonClientException):
        AsyncRunClient(owner=OWNER, project=PROJECT, client=SyncPolyaxonClientMock())


def test_async_run_client_method_surface_is_async():
    for method in ASYNC_METHODS:
        assert method in AsyncRunClient.__dict__
        if method == "watch_statuses":
            assert inspect.isasyncgenfunction(getattr(AsyncRunClient, method))
        else:
            assert inspect.iscoroutinefunction(getattr(AsyncRunClient, method))


def test_async_run_client_local_helpers_stay_shared():
    helpers = [
        "_apply_created_run",
        "_apply_offline_status",
        "_build_artifact_lineage_body",
        "_build_restart_body",
        "_build_resume_body",
        "_build_run_create_body",
        "_build_runs_io_data",
        "_build_status_condition",
        "_build_tags_patch",
        "_build_values_patch",
        "_cache_offline_artifact_lineage",
        "_normalize_operation_content",
        "_sanitize_filename",
        "_set_transferred_project",
    ]
    for helper in helpers:
        assert getattr(AsyncRunClient, helper) is getattr(RunClient, helper)
        assert not inspect.iscoroutinefunction(getattr(AsyncRunClient, helper))


@pytest.mark.asyncio
async def test_refresh_data_loads_nested_data_sequentially():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    events = []

    async def get_run(owner, project, run_uuid):
        events.append("run")
        return make_run(status=V1Statuses.RUNNING)

    async def get_run_statuses(owner, project, run_uuid):
        events.append("statuses")
        return mock.Mock(
            status=V1Statuses.RUNNING,
            status_conditions=[
                V1StatusCondition.model_construct(type=V1Statuses.RUNNING)
            ],
        )

    async def get_run_artifacts_lineage(owner, project, run_uuid, **kwargs):
        events.append("lineage")
        return mock.Mock(results=[V1RunArtifact.model_construct(name="model")])

    async def get_run_events(*args, **kwargs):
        events.append("metrics")
        return mock.Mock(data=[{"name": "loss", "events": []}])

    sdk_client.runs_v1.get_run = get_run
    sdk_client.runs_v1.get_run_statuses = get_run_statuses
    sdk_client.runs_v1.get_run_artifacts_lineage = get_run_artifacts_lineage
    sdk_client.runs_v1.get_run_events = get_run_events
    client = make_client(sdk_client)

    await client.refresh_data(
        load_conditions=True,
        load_artifacts_lineage=True,
        load_metrics=True,
    )

    assert events == ["run", "statuses", "lineage", "metrics"]
    assert client.status == V1Statuses.RUNNING
    assert set(client.artifacts_lineage.keys()) == {"model"}
    assert set(client._metric_names) == {"loss"}


@pytest.mark.asyncio
async def test_refresh_data_returns_none_when_offline():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.get_run = AsyncMock()
    client = AsyncRunClient(
        owner=OWNER,
        project=PROJECT,
        client=sdk_client,
        is_offline=True,
    )

    assert await client.refresh_data() is None
    assert sdk_client.runs_v1.get_run.call_count == 0


@pytest.mark.asyncio
async def test_update_awaits_api_without_async_req_and_mutates_state():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = make_run(description="updated")
    sdk_client.runs_v1.patch_run = AsyncMock(return_value=response)
    client = make_client(sdk_client)

    result = await client.update({"description": "updated"})

    assert result is response
    assert client.run_data is response
    sdk_client.runs_v1.patch_run.assert_called_once_with(
        owner=OWNER,
        project=PROJECT,
        run_uuid=RUN_UUID,
        body={"description": "updated"},
    )
    assert "async_req" not in sdk_client.runs_v1.patch_run.call_args[1]


@pytest.mark.asyncio
async def test_metadata_methods_await_api_without_overwriting_local_state():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.patch_run = AsyncMock(return_value=make_run(name="remote"))
    client = make_client(sdk_client)

    await client.set_name("local-name")
    await client.log_inputs(alpha=1)
    await client.log_outputs(metric=0.1)
    await client.log_meta(flag=True)
    await client.log_tags(["tag1"])

    assert sdk_client.runs_v1.patch_run.call_count == 5
    assert client.run_data.name == "local-name"
    assert client.run_data.inputs == {"alpha": 1}
    assert client.run_data.outputs == {"metric": 0.1}
    assert client.run_data.meta_info == {"flag": True}
    assert client.run_data.tags == ["tag1"]
    for call in sdk_client.runs_v1.patch_run.call_args_list:
        assert "async_req" not in call[1]


@pytest.mark.asyncio
async def test_create_awaits_api_without_async_req_and_mutates_state():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    created = make_run(name="created")
    sdk_client.runs_v1.create_run = AsyncMock(return_value=created)
    client = make_client(sdk_client)

    result = await client.create(name="created", tags=["tag1"])

    assert result is created
    assert client.run_uuid == RUN_UUID
    assert client.status == V1Statuses.CREATED
    sdk_client.runs_v1.create_run.assert_called_once()
    assert sdk_client.runs_v1.create_run.call_args[1]["owner"] == OWNER
    assert sdk_client.runs_v1.create_run.call_args[1]["project"] == PROJECT
    assert "async_req" not in sdk_client.runs_v1.create_run.call_args[1]


@pytest.mark.asyncio
async def test_status_methods_await_api_without_async_req():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_status = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    assert await client.start() is None

    sdk_client.runs_v1.create_run_status.assert_called_once()
    assert sdk_client.runs_v1.create_run_status.call_args[1]["owner"] == OWNER
    assert sdk_client.runs_v1.create_run_status.call_args[1]["project"] == PROJECT
    assert sdk_client.runs_v1.create_run_status.call_args[1]["uuid"] == RUN_UUID
    condition = sdk_client.runs_v1.create_run_status.call_args[1]["body"]["condition"]
    assert condition.type == V1Statuses.RUNNING
    assert "async_req" not in sdk_client.runs_v1.create_run_status.call_args[1]


@pytest.mark.asyncio
async def test_wait_for_condition_updates_status():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.get_run_statuses = AsyncMock(
        return_value=mock.Mock(
            status=V1Statuses.RUNNING,
            status_conditions=[
                V1StatusCondition.model_construct(type=V1Statuses.RUNNING)
            ],
        )
    )
    client = make_client(sdk_client)

    await client.wait_for_condition(statuses=[V1Statuses.RUNNING])

    assert client.status == V1Statuses.RUNNING
    sdk_client.runs_v1.get_run_statuses.assert_called_once_with(
        OWNER,
        PROJECT,
        RUN_UUID,
    )


@pytest.mark.asyncio
async def test_watch_statuses_yields_until_done_status():
    patch_settings()
    settings.CLIENT_CONFIG.watch_interval = 0
    sdk_client = AsyncPolyaxonClientMock()
    running_condition = V1StatusCondition.model_construct(type=V1Statuses.RUNNING)
    succeeded_condition = V1StatusCondition.model_construct(type=V1Statuses.SUCCEEDED)
    sdk_client.runs_v1.get_run_statuses = AsyncMock(
        side_effect=[
            mock.Mock(
                status=V1Statuses.RUNNING,
                status_conditions=[running_condition],
            ),
            mock.Mock(
                status=V1Statuses.SUCCEEDED,
                status_conditions=[running_condition, succeeded_condition],
            ),
        ]
    )
    client = make_client(sdk_client)

    statuses = []
    async for status, _conditions in client.watch_statuses():
        statuses.append(status)

    assert statuses == [V1Statuses.RUNNING, V1Statuses.SUCCEEDED]
    assert client.status == V1Statuses.SUCCEEDED
    assert sdk_client.runs_v1.get_run_statuses.call_count == 2


@pytest.mark.asyncio
async def test_get_logs_awaits_refresh_and_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = mock.Mock()
    sdk_client.runs_v1.get_run = AsyncMock(return_value=make_run())
    sdk_client.runs_v1.get_run_logs = AsyncMock(return_value=response)
    client = make_client(sdk_client)
    client._run_data.settings = None

    result = await client.get_logs(last_file="last.log", last_time="123")

    assert result is response
    sdk_client.runs_v1.get_run.assert_called_once_with(OWNER, PROJECT, RUN_UUID)
    assert sdk_client.runs_v1.get_run_logs.call_args[0] == (
        "test-namespace",
        OWNER,
        PROJECT,
        RUN_UUID,
    )
    assert "async_req" not in sdk_client.runs_v1.get_run_logs.call_args[1]


@pytest.mark.asyncio
async def test_inspect_awaits_refresh_and_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = {"pods": {}}
    sdk_client.runs_v1.get_run = AsyncMock(
        return_value=make_run(status=V1Statuses.RUNNING)
    )
    sdk_client.runs_v1.inspect_run = AsyncMock(return_value=response)
    client = make_client(sdk_client)
    client._run_data.settings = None

    result = await client.inspect()

    assert result is response
    sdk_client.runs_v1.get_run.assert_called_once_with(OWNER, PROJECT, RUN_UUID)
    assert sdk_client.runs_v1.inspect_run.call_args[0] == (
        "test-namespace",
        OWNER,
        PROJECT,
        RUN_UUID,
        None,
    )
    assert "async_req" not in sdk_client.runs_v1.inspect_run.call_args[1]


@pytest.mark.asyncio
async def test_events_metrics_and_lineage_methods_await_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.get_run_events = AsyncMock(
        return_value=mock.Mock(data=[{"name": "accuracy", "events": []}])
    )
    sdk_client.runs_v1.get_multi_run_events = AsyncMock(return_value=mock.Mock())
    sdk_client.runs_v1.get_run_artifacts_lineage = AsyncMock(
        return_value=mock.Mock(results=[])
    )
    sdk_client.runs_v1.get_runs_artifacts_lineage = AsyncMock(return_value=mock.Mock())
    client = make_client(sdk_client)
    client._run_data = make_run()

    metrics = await client.get_metrics(["accuracy"], force=True)
    await client.get_multi_run_events(
        kind=V1ArtifactKind.METRIC,
        runs=[RUN_UUID],
        names=["accuracy"],
    )
    await client.get_artifacts_lineage(limit=5)
    await client.get_runs_artifacts_lineage(query="kind:model")

    assert metrics["accuracy"]["name"] == "accuracy"
    sdk_client.runs_v1.get_run_events.assert_called_once_with(
        "test-namespace",
        OWNER,
        PROJECT,
        RUN_UUID,
        kind=V1ArtifactKind.METRIC,
        names=["accuracy"],
        orient=V1Events.ORIENT_DICT,
        force=True,
    )
    assert sdk_client.runs_v1.get_multi_run_events.call_args[0] == (
        "test-namespace",
        OWNER,
        PROJECT,
    )
    sdk_client.runs_v1.get_run_artifacts_lineage.assert_called_once_with(
        OWNER,
        PROJECT,
        RUN_UUID,
        limit=5,
    )
    sdk_client.runs_v1.get_runs_artifacts_lineage.assert_called_once_with(
        OWNER,
        PROJECT,
        limit=20,
        query="kind:model",
    )


@pytest.mark.asyncio
async def test_run_action_methods_await_api_without_async_req():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    for sdk_method_name in ["stop_run", "skip_run", "approve_run", "invalidate_run"]:
        setattr(sdk_client.runs_v1, sdk_method_name, AsyncMock(return_value=None))
    client = make_client(sdk_client)

    assert await client.stop() is None
    assert await client.skip() is None
    assert await client.approve() is None
    assert await client.invalidate() is None

    for sdk_method_name in ["stop_run", "skip_run", "approve_run", "invalidate_run"]:
        sdk_method = getattr(sdk_client.runs_v1, sdk_method_name)
        sdk_method.assert_called_once_with(OWNER, PROJECT, RUN_UUID)
        assert "async_req" not in sdk_method.call_args[1]


@pytest.mark.asyncio
async def test_list_delete_namespace_and_transfer_await_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    runs = V1ListRunsResponse(results=[])
    all_runs = V1ListRunsResponse(results=[])
    sdk_client.runs_v1.list_runs = AsyncMock(return_value=runs)
    sdk_client.organizations_v1.get_organization_runs = AsyncMock(return_value=all_runs)
    sdk_client.runs_v1.delete_run = AsyncMock(return_value=None)
    sdk_client.runs_v1.get_run_namespace = AsyncMock(
        return_value=mock.Mock(namespace="ns")
    )
    sdk_client.runs_v1.transfer_run = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    assert await client.list(limit=10, query="status:running") is runs
    assert await client.list(all_projects=True) is all_runs
    assert await client.list_children(query="kind:job") is runs
    assert await client.get_namespace() == "ns"
    assert await client.delete() is None
    assert await client.transfer("target-project") is None

    sdk_client.runs_v1.list_runs.assert_any_call(
        OWNER,
        PROJECT,
        limit=10,
        query="status:running",
    )
    sdk_client.organizations_v1.get_organization_runs.assert_called_once_with(
        OWNER,
        limit=20,
    )
    assert sdk_client.runs_v1.list_runs.call_args_list[1][1]["query"] == (
        "kind:job,pipeline:{}".format(RUN_UUID)
    )
    sdk_client.runs_v1.get_run_namespace.assert_called_once_with(
        OWNER,
        PROJECT,
        RUN_UUID,
    )
    sdk_client.runs_v1.delete_run.assert_called_once_with(OWNER, PROJECT, RUN_UUID)
    sdk_client.runs_v1.transfer_run.assert_called_once_with(
        owner=OWNER,
        project=PROJECT,
        run_uuid=RUN_UUID,
        body={"project": "target-project"},
    )
    assert client.project == "target-project"


@pytest.mark.asyncio
async def test_log_artifact_lineage_and_run_edges_await_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_artifacts_lineage = AsyncMock(return_value=None)
    sdk_client.runs_v1.set_run_edges_lineage = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    assert (
        await client.log_artifact_lineage(V1RunArtifact.model_construct(name="model"))
        is None
    )
    assert await client.set_run_edges_lineage([]) is None

    sdk_client.runs_v1.create_run_artifacts_lineage.assert_called_once()
    assert (
        "async_req" not in sdk_client.runs_v1.create_run_artifacts_lineage.call_args[1]
    )
    sdk_client.runs_v1.set_run_edges_lineage.assert_called_once()
    assert "async_req" not in sdk_client.runs_v1.set_run_edges_lineage.call_args[1]


@pytest.mark.asyncio
async def test_log_code_ref_detects_code_ref_in_thread(monkeypatch):
    patch_settings()
    monkeypatch.setattr(
        "polyaxon._client.run.get_code_reference",
        lambda: {"commit": "abc123", "branch": "main"},
    )
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_artifacts_lineage = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    await client.log_code_ref(is_input=False)

    artifact = get_logged_lineage_artifact(sdk_client)
    assert artifact.name == "abc123"
    assert artifact.kind == V1ArtifactKind.CODEREF
    assert artifact.summary == {"commit": "abc123", "branch": "main"}
    assert artifact.is_input is False


@pytest.mark.asyncio
async def test_log_data_ref_hashes_content_and_awaits_lineage_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_artifacts_lineage = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    await client.log_data_ref(
        name="dataset",
        content={"x": 1},
        summary={"rows": 10},
    )

    artifact = get_logged_lineage_artifact(sdk_client)
    assert artifact.name == "dataset"
    assert artifact.kind == V1ArtifactKind.DATA
    assert artifact.summary == {"rows": 10, "hash": hash_value({"x": 1})}
    assert artifact.is_input is True


@pytest.mark.asyncio
async def test_log_artifact_ref_hashes_existing_file(tmp_path):
    patch_settings()
    asset = tmp_path / "result.json"
    asset.write_text("payload")
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_artifacts_lineage = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    await client.log_artifact_ref(
        path=str(asset),
        kind=V1ArtifactKind.ARTIFACT,
    )

    artifact = get_logged_lineage_artifact(sdk_client)
    assert artifact.name == "result"
    assert artifact.kind == V1ArtifactKind.ARTIFACT
    assert artifact.path == str(asset)
    assert artifact.summary == {"path": str(asset), "hash": hash_file(str(asset))}


@pytest.mark.asyncio
async def test_log_model_ref_updates_meta_and_awaits_lineage_api():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.patch_run = AsyncMock(return_value=make_run())
    sdk_client.runs_v1.create_run_artifacts_lineage = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    await client.log_model_ref(
        path="models/model.pt",
        name="model",
        framework="pytorch",
        summary={"hash": "hash2"},
        rel_path="models/model.pt",
    )

    assert client.run_data.meta_info == {"has_model": True}
    sdk_client.runs_v1.patch_run.assert_called_once()
    artifact = get_logged_lineage_artifact(sdk_client)
    assert artifact.name == "model"
    assert artifact.kind == V1ArtifactKind.MODEL
    assert artifact.path == "models/model.pt"
    assert artifact.summary == {
        "hash": "hash2",
        "framework": "pytorch",
        "path": "models/model.pt",
    }


@pytest.mark.asyncio
async def test_log_file_and_dir_refs_hash_paths_and_await_lineage_api(tmp_path):
    patch_settings()
    file_path = tmp_path / "file.txt"
    file_path.write_text("payload")
    dir_path = tmp_path / "outputs"
    dir_path.mkdir()
    (dir_path / "data.txt").write_text("data")
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_artifacts_lineage = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    await client.log_file_ref(str(file_path), is_input=True)
    await client.log_dir_ref(str(dir_path), name="outputs")

    file_artifact = get_logged_lineage_artifact(sdk_client, 0)
    dir_artifact = get_logged_lineage_artifact(sdk_client, 1)
    assert file_artifact.name == "file"
    assert file_artifact.kind == V1ArtifactKind.FILE
    assert file_artifact.is_input is True
    assert file_artifact.summary == {
        "path": str(file_path),
        "hash": hash_file(str(file_path)),
    }
    assert dir_artifact.name == "outputs"
    assert dir_artifact.kind == V1ArtifactKind.DIR
    assert dir_artifact.summary["path"] == str(dir_path)
    assert dir_artifact.summary["hash"]


@pytest.mark.asyncio
async def test_log_tensorboard_ref_logs_once_and_sets_meta():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.patch_run = AsyncMock(return_value=make_run())
    sdk_client.runs_v1.create_run_artifacts_lineage = AsyncMock(return_value=None)
    client = make_client(sdk_client)

    await client.log_tensorboard_ref("tensorboard", rel_path="tensorboard")
    await client.log_tensorboard_ref("tensorboard", rel_path="tensorboard")

    assert client.run_data.meta_info == {"has_tensorboard": True}
    assert sdk_client.runs_v1.patch_run.call_count == 1
    assert sdk_client.runs_v1.create_run_artifacts_lineage.call_count == 1
    artifact = get_logged_lineage_artifact(sdk_client)
    assert artifact.name == "tensorboard"
    assert artifact.kind == V1ArtifactKind.TENSORBOARD
    assert artifact.path == "tensorboard"
    assert artifact.summary == {"path": "tensorboard"}


@pytest.mark.asyncio
async def test_promote_methods_use_async_project_client_with_injected_client():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.projects_v1 = mock.MagicMock()
    sdk_client.projects_v1.get_version = AsyncMock(
        side_effect=ApiException(status=404, reason="missing")
    )
    sdk_client.projects_v1.create_version = AsyncMock(
        return_value=V1ProjectVersion.model_construct(name="v1")
    )
    client = make_client(sdk_client)

    result = await client.promote_to_model_version("v1")

    assert result.name == "v1"
    sdk_client.projects_v1.create_version.assert_called_once()
    assert sdk_client.projects_v1.create_version.call_args[0] == (
        OWNER,
        PROJECT,
        V1ProjectVersionKind.MODEL,
    )
    body = sdk_client.projects_v1.create_version.call_args[1]["body"]
    assert body.run == RUN_UUID


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,args",
    [
        ("upload_artifact", ("file.txt",)),
        ("download_artifacts", ()),
        ("persist_run", ("/tmp/run",)),
        ("push_offline_run", ("/tmp/run",)),
        ("get_runs_as_hiplot", ()),
    ],
)
async def test_sync_only_methods_raise(method, args):
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    client = make_client(sdk_client)

    with pytest.raises(PolyaxonClientException):
        await getattr(client, method)(*args)


@pytest.mark.asyncio
async def test_load_offline_run_is_sync_only():
    patch_settings()

    with pytest.raises(PolyaxonClientException):
        await AsyncRunClient.load_offline_run("/tmp/run")


@pytest.mark.asyncio
async def test_restart_routes_to_copy_when_copy_flag_set():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = make_run(name="restarted")
    sdk_client.runs_v1.copy_run = AsyncMock(return_value=response)
    sdk_client.runs_v1.restart_run = AsyncMock()
    client = make_client(sdk_client)

    result = await client.restart(copy=True, name="restarted")

    assert result is response
    assert sdk_client.runs_v1.copy_run.call_count == 1
    assert sdk_client.runs_v1.restart_run.call_count == 0
    assert "async_req" not in sdk_client.runs_v1.copy_run.call_args[1]


@pytest.mark.asyncio
async def test_restart_routes_to_restart_when_copy_not_set():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = make_run(name="restarted")
    sdk_client.runs_v1.restart_run = AsyncMock(return_value=response)
    sdk_client.runs_v1.copy_run = AsyncMock()
    client = make_client(sdk_client)

    result = await client.restart(name="restarted")

    assert result is response
    assert sdk_client.runs_v1.restart_run.call_count == 1
    assert sdk_client.runs_v1.copy_run.call_count == 0
    assert "async_req" not in sdk_client.runs_v1.restart_run.call_args[1]


@pytest.mark.asyncio
async def test_resume_awaits_resume_run_with_built_body():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    response = make_run(name="resumed")
    sdk_client.runs_v1.resume_run = AsyncMock(return_value=response)
    client = make_client(sdk_client)

    result = await client.resume(name="resumed")

    assert result is response
    assert sdk_client.runs_v1.resume_run.call_count == 1
    assert "async_req" not in sdk_client.runs_v1.resume_run.call_args[1]


@pytest.mark.asyncio
async def test_log_succeeded_awaits_create_run_status_via_log_status():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_status = AsyncMock(return_value=None)
    client = make_client(sdk_client)
    client._run_data = make_run(status=V1Statuses.RUNNING)

    await client.log_succeeded()

    assert sdk_client.runs_v1.create_run_status.call_count == 1
    body = sdk_client.runs_v1.create_run_status.call_args[1]["body"]
    assert body["condition"].type == V1Statuses.SUCCEEDED


@pytest.mark.asyncio
async def test_log_end_status_short_circuits_when_already_done():
    patch_settings()
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.runs_v1.create_run_status = AsyncMock()
    client = make_client(sdk_client)
    client._run_data = make_run(status=V1Statuses.SUCCEEDED)

    await client.log_failed()

    assert sdk_client.runs_v1.create_run_status.call_count == 0
