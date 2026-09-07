import inspect
from pathlib import Path
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from polyaxon import settings
from polyaxon._client.run import AsyncRunClient, RunClient
from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import ENV_KEYS_RUN_INSTANCE
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon.exceptions import PolyaxonClientException


pytestmark = pytest.mark.client_mark

OWNER = "owner"
PROJECT = "project-b"
CACHED_PROJECT = "project-a"
CACHED_UUID = "11111111111111111111111111111111"
NEW_UUID = "22222222222222222222222222222222"
CLIENT_TYPES = [RunClient, AsyncRunClient, SandboxClient, AsyncSandboxClient]
RUN_CLIENT_TYPES = [RunClient, AsyncRunClient]


@pytest.fixture(autouse=True)
def isolate_context(tmp_path, monkeypatch):
    local_path = tmp_path / "local"
    local_path.mkdir()
    monkeypatch.chdir(local_path)
    for manager in (ProjectConfigManager, RunConfigManager):
        monkeypatch.setattr(manager, "CONFIG_PATH", str(tmp_path / "global"))
    monkeypatch.setattr(settings, "CLIENT_CONFIG", ClientConfig(host="http://polyaxon"))
    monkeypatch.delenv(ENV_KEYS_RUN_INSTANCE, raising=False)


@pytest.fixture
def cache_run():
    def cache(owner=OWNER, project=CACHED_PROJECT, visibility="local"):
        RunConfigManager.set_config(
            V1Run(uuid=CACHED_UUID, owner=owner, project=project),
            visibility=visibility,
        )
        return str(Path(RunConfigManager.get_config_filepath(create=False)).resolve())

    return cache


@pytest.fixture
def make_client():
    def make(client_type, **kwargs):
        sdk = SimpleNamespace(
            is_async=client_type._IS_ASYNC,
            config=None,
            runs_v1=MagicMock(),
            sandbox_v1=MagicMock(),
        )
        if sdk.is_async:
            for method in (
                "create_run",
                "get_run_namespace",
                "list_runs",
                "transfer_run",
            ):
                setattr(sdk.runs_v1, method, AsyncMock())
        kwargs.setdefault("owner", OWNER)
        kwargs.setdefault("project", PROJECT)
        return client_type(client=sdk, **kwargs), sdk

    return make


async def call_client(method, *args, **kwargs):
    response = method(*args, **kwargs)
    if inspect.isawaitable(response):
        return await response
    return response


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
@pytest.mark.parametrize(
    "owner,project", [(OWNER, CACHED_PROJECT), ("other-owner", PROJECT)]
)
async def test_cached_mismatch_rejected_before_run_request(
    client_type, owner, project, cache_run, make_client
):
    cache_path = cache_run(owner=owner, project=project)
    client, sdk = make_client(client_type)

    assert client.run_data.uuid == CACHED_UUID
    with pytest.raises(PolyaxonClientException) as exc:
        await call_client(client.get_namespace)

    message = str(exc.value)
    assert f"{OWNER}/{PROJECT}" in message
    assert f"{owner}/{project}" in message
    assert cache_path in message
    sdk.runs_v1.get_run_namespace.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
async def test_local_project_does_not_accept_unrelated_global_run(
    client_type, cache_run, make_client
):
    cache_run(visibility="global")
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    client, sdk = make_client(client_type, owner=None, project=None)

    assert (client.owner, client.project) == (OWNER, PROJECT)
    with pytest.raises(PolyaxonClientException):
        await call_client(client.get_namespace)

    sdk.runs_v1.get_run_namespace.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
@pytest.mark.parametrize(
    "owner,project", [(OWNER, PROJECT), (OWNER, None), (None, PROJECT), (None, None)]
)
async def test_matching_or_incomplete_cache_keeps_existing_run_access(
    client_type, owner, project, cache_run, make_client
):
    cache_run(owner=owner, project=project)
    client, sdk = make_client(client_type)
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    assert await call_client(client.get_namespace) == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(OWNER, PROJECT, CACHED_UUID)


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
@pytest.mark.parametrize("infer_project", [True, False])
async def test_explicit_uuid_overrides_conflicting_cache(
    client_type, infer_project, cache_run, make_client
):
    cache_run()
    kwargs = {}
    if infer_project:
        ProjectConfigManager.set_config(
            V1Project(owner=OWNER, name=PROJECT), visibility="local"
        )
        kwargs.update(owner=None, project=None)
    client, sdk = make_client(client_type, run_uuid=NEW_UUID, **kwargs)
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    assert await call_client(client.get_namespace) == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(OWNER, PROJECT, NEW_UUID)


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
async def test_list_does_not_consume_cached_run(client_type, cache_run, make_client):
    cache_run()
    client, sdk = make_client(client_type)
    response = SimpleNamespace(results=[])
    sdk.runs_v1.list_runs.return_value = response

    assert await call_client(client.list) is response
    assert sdk.runs_v1.list_runs.call_args.args == (OWNER, PROJECT)
    with pytest.raises(PolyaxonClientException):
        _ = client.run_uuid


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
async def test_create_replaces_conflicting_cached_run(
    client_type, cache_run, make_client
):
    cache_run()
    client, sdk = make_client(client_type)
    created = V1Run(uuid=NEW_UUID, owner=OWNER, project=PROJECT)
    sdk.runs_v1.create_run.return_value = created
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    assert await call_client(client.create, name="new-run") is created
    assert client.run_uuid == NEW_UUID
    assert sdk.runs_v1.create_run.call_args.kwargs["project"] == PROJECT
    assert await call_client(client.get_namespace) == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(OWNER, PROJECT, NEW_UUID)


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
async def test_failed_creation_preserves_cached_conflict(
    client_type, cache_run, make_client
):
    cache_run()
    client, sdk = make_client(client_type)
    sdk.runs_v1.create_run.side_effect = RuntimeError("creation failed")

    with pytest.raises(RuntimeError, match="creation failed"):
        await call_client(client.create)

    assert client.run_data.uuid == CACHED_UUID
    with pytest.raises(PolyaxonClientException):
        await call_client(client.get_namespace)
    sdk.runs_v1.get_run_namespace.assert_not_called()


@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
def test_set_run_uuid_replaces_conflicting_cache(client_type, cache_run, make_client):
    cache_run()
    client, _ = make_client(client_type)

    client.set_run_uuid(NEW_UUID)

    assert client.run_uuid == NEW_UUID


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
async def test_successful_transfer_releases_cached_project_identity(
    client_type, cache_run, make_client
):
    cache_run(project=PROJECT)
    client, sdk = make_client(client_type)
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    await call_client(client.transfer, CACHED_PROJECT)

    assert client.project == CACHED_PROJECT
    assert client.run_data.project == CACHED_PROJECT
    assert client.run_uuid == CACHED_UUID
    assert await call_client(client.get_namespace) == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(
        OWNER, CACHED_PROJECT, CACHED_UUID
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
async def test_failed_transfer_keeps_cached_project_identity(
    client_type, cache_run, make_client
):
    cache_run(project=PROJECT)
    client, sdk = make_client(client_type)
    sdk.runs_v1.transfer_run.side_effect = RuntimeError("transfer failed")

    with pytest.raises(RuntimeError, match="transfer failed"):
        await call_client(client.transfer, CACHED_PROJECT)

    assert client.project == PROJECT
    assert client.run_uuid == CACHED_UUID
    client.set_project(CACHED_PROJECT)
    with pytest.raises(PolyaxonClientException):
        _ = client.run_uuid


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
async def test_offline_run_does_not_reuse_cached_uuid(
    client_type, cache_run, make_client
):
    cache_run()
    client, sdk = make_client(client_type, is_offline=True)

    assert client.run_uuid
    assert client.run_uuid != CACHED_UUID
    assert await call_client(client.get_namespace) is None
    sdk.runs_v1.get_run_namespace.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", [SandboxClient, AsyncSandboxClient])
async def test_offline_sandbox_preserves_cached_uuid(
    client_type, cache_run, make_client
):
    cache_run()
    client, sdk = make_client(client_type, is_offline=True)

    assert client.run_uuid == CACHED_UUID
    assert await call_client(client.get_namespace) is None
    sdk.runs_v1.get_run_namespace.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
async def test_no_op_does_not_consume_cached_context(
    client_type, cache_run, make_client
):
    cache_run()
    client, sdk = make_client(client_type, no_op=True)

    assert await call_client(client.get_namespace) is None
    sdk.runs_v1.get_run_namespace.assert_not_called()


@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
def test_managed_run_identity_does_not_reuse_cached_uuid(
    client_type, cache_run, make_client, monkeypatch
):
    cache_run()
    settings.CLIENT_CONFIG.is_managed = True
    monkeypatch.setenv(ENV_KEYS_RUN_INSTANCE, f"{OWNER}.{PROJECT}.runs.{NEW_UUID}")

    client, _ = make_client(client_type, owner=None, project=None)

    assert (client.owner, client.project, client.run_uuid) == (
        OWNER,
        PROJECT,
        NEW_UUID,
    )


def test_loading_offline_run_replaces_cached_identity(cache_run, make_client, tmp_path):
    cache_run()
    client, _ = make_client(RunClient)
    persisted = V1Run(uuid=NEW_UUID, owner=OWNER, project=PROJECT)
    (tmp_path / ctx_paths.CONTEXT_LOCAL_RUN).write_text(persisted.to_json())

    restored = RunClient.load_offline_run(path=str(tmp_path), run_client=client)

    assert restored is client
    assert client.run_uuid == NEW_UUID


@pytest.mark.parametrize("is_new", [True, False])
def test_tracking_new_run_choice_preserves_cached_conflict(
    is_new, cache_run, monkeypatch, tmp_path
):
    from traceml.tracking.run import Run

    cache_run()
    sdk = SimpleNamespace(is_async=False, config=None, runs_v1=MagicMock())
    sdk.runs_v1.create_run.return_value = V1Run(
        uuid=NEW_UUID, owner=OWNER, project=PROJECT
    )
    monkeypatch.setattr(Run, "_set_exit_handler", MagicMock())

    client = Run(
        owner=OWNER,
        project=PROJECT,
        client=sdk,
        is_new=is_new,
        track_code=False,
        track_env=False,
        track_logs=False,
        artifacts_path=str(tmp_path / "artifacts"),
        collect_artifacts=False,
        collect_resources=False,
    )

    if is_new:
        assert client.run_uuid == NEW_UUID
        sdk.runs_v1.create_run.assert_called_once()
    else:
        assert client.run_data.uuid == CACHED_UUID
        with pytest.raises(PolyaxonClientException):
            client.get_namespace()
        sdk.runs_v1.create_run.assert_not_called()
        sdk.runs_v1.get_run_namespace.assert_not_called()
