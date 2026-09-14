import inspect
import logging
from pathlib import Path
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from clipped.formatting import Printer
from polyaxon import settings
from polyaxon._cli.context import _get_client_context
from polyaxon._client.run import AsyncRunClient, RunClient
from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import ENV_KEYS_RUN_INSTANCE
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_user import V1User
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError


pytestmark = pytest.mark.client_mark

OWNER = "owner"
PROJECT = "project-b"
CACHED_PROJECT = "project-a"
CACHED_UUID = "11111111111111111111111111111111"
NEW_UUID = "22222222222222222222222222222222"
CLIENT_TYPES = [RunClient, AsyncRunClient, SandboxClient, AsyncSandboxClient]
CONTEXT_CLIENT_TYPES = [RunClient, SandboxClient]
RUN_CLIENT_TYPES = [RunClient, AsyncRunClient]


@pytest.fixture(autouse=True)
def isolate_context(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="polyaxon.cli")
    monkeypatch.setattr(Printer.stderr_console, "width", 200)
    local_path = tmp_path / "local"
    local_path.mkdir()
    monkeypatch.chdir(local_path)
    for manager in (ProjectConfigManager, RunConfigManager, UserConfigManager):
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


@pytest.mark.parametrize(
    "visibility,log_context,team",
    [
        pytest.param("local", False, None, id="opt-out"),
        pytest.param("local", True, "team", id="local-team"),
        pytest.param("global", True, None, id="global"),
    ],
)
@pytest.mark.parametrize("client_type", CONTEXT_CLIENT_TYPES)
def test_cached_project_logging_is_opt_in(
    client_type, visibility, log_context, team, make_client, caplog, capsys
):
    owner = f"{OWNER}/{team}" if team else OWNER
    ProjectConfigManager.set_config(
        V1Project(owner=owner, name=PROJECT), visibility=visibility
    )
    cache_path = str(
        Path(ProjectConfigManager.get_config_filepath(create=False)).resolve()
    )
    client, _ = make_client(
        client_type,
        owner=None,
        project=None,
        run_uuid=NEW_UUID,
        log_context=log_context,
    )

    assert (client.owner, client.project, client.run_uuid) == (OWNER, PROJECT, NEW_UUID)
    assert client.team == team
    fields, _ = _get_client_context(client)
    assert fields[0][1] == owner
    notices = [r for r in caplog.records if "Using cached" in r.getMessage()]
    assert len(notices) == int(log_context)
    if log_context:
        assert notices[0].levelno == logging.INFO
        assert f"Using cached project `{owner}/{PROJECT}`" in notices[0].getMessage()
        assert cache_path in notices[0].getMessage()
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_explicit_project_team_is_preserved(make_client):
    client, _ = make_client(
        RunClient,
        owner=None,
        project=f"{OWNER}/team/{PROJECT}",
        run_uuid=NEW_UUID,
    )

    assert (client.owner, client.team, client.project) == (OWNER, "team", PROJECT)
    fields, _ = _get_client_context(client)
    assert fields[0][1] == f"{OWNER}/team"
    assert fields[0][2].kind == "explicit"
    assert fields[0][2].path is None


@pytest.mark.parametrize("infer_project", [False, True])
def test_cached_owner_logging_keeps_its_own_source(
    infer_project, make_client, caplog, capsys
):
    UserConfigManager.set_config(V1User(organization=OWNER))
    owner_path = str(
        Path(UserConfigManager.get_config_filepath(create=False)).resolve()
    )
    if infer_project:
        ProjectConfigManager.set_config(V1Project(name=PROJECT), visibility="local")
    client, _ = make_client(
        RunClient,
        owner=None,
        project=None if infer_project else PROJECT,
        run_uuid=NEW_UUID,
        log_context=True,
    )

    assert (client.owner, client.project, client.run_uuid) == (OWNER, PROJECT, NEW_UUID)
    assert caplog.text.count(f"Using cached owner `{OWNER}`") == 1
    assert owner_path in caplog.text
    assert caplog.text.count(f"Using cached project `{PROJECT}`") == int(infer_project)
    assert f"Using cached project `{OWNER}/{PROJECT}`" not in caplog.text
    if infer_project:
        project_path = str(
            Path(ProjectConfigManager.get_config_filepath(create=False)).resolve()
        )
        assert project_path in caplog.text
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_context_logging_keeps_invalid_projects_as_schema_errors(
    make_client, caplog, capsys
):
    with pytest.raises(PolyaxonSchemaError, match="invalid project"):
        make_client(RunClient, project="invalid project", log_context=True)

    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert "Using cached" not in caplog.text


@pytest.mark.parametrize(
    "owner,project", [(OWNER, CACHED_PROJECT), ("other-owner", PROJECT)]
)
def test_cached_mismatch_rejected_before_run_request(
    owner, project, cache_run, make_client, caplog
):
    cache_path = cache_run(owner=owner, project=project)
    client, sdk = make_client(RunClient, log_context=True)

    assert client.run_data.uuid == CACHED_UUID
    with pytest.raises(PolyaxonClientException) as exc:
        client.get_namespace()

    message = str(exc.value)
    assert f"{OWNER}/{PROJECT}" in message
    assert f"{owner}/{project}" in message
    assert f"local cache · {cache_path}" in message
    assert "owner: explicit; project: explicit" in message
    sdk.runs_v1.get_run_namespace.assert_not_called()
    assert "Using cached run" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
async def test_cached_mismatch_rejected_across_client_types(
    client_type, cache_run, make_client
):
    cache_run()
    client, sdk = make_client(client_type)

    with pytest.raises(PolyaxonClientException):
        await call_client(client.get_namespace)

    sdk.runs_v1.get_run_namespace.assert_not_called()


def test_local_project_does_not_accept_unrelated_global_run(cache_run, make_client):
    cache_run(visibility="global")
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    client, sdk = make_client(RunClient, owner=None, project=None)

    assert (client.owner, client.project) == (OWNER, PROJECT)
    with pytest.raises(PolyaxonClientException):
        client.get_namespace()

    sdk.runs_v1.get_run_namespace.assert_not_called()


@pytest.mark.parametrize("owner,project", [(OWNER, PROJECT), (OWNER, None)])
def test_matching_or_incomplete_cache_keeps_existing_run_access(
    owner, project, cache_run, make_client, caplog
):
    cache_path = cache_run(owner=owner, project=project)
    client, sdk = make_client(RunClient, log_context=True)
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    assert "Using cached run" not in caplog.text
    assert client.get_namespace() == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(OWNER, PROJECT, CACHED_UUID)
    assert client.run_uuid == CACHED_UUID
    notices = [r for r in caplog.records if "Using cached run" in r.getMessage()]
    assert len(notices) == 1
    assert notices[0].levelno == (
        logging.INFO if owner and project else logging.WARNING
    )
    assert CACHED_UUID in notices[0].getMessage()
    assert cache_path in notices[0].getMessage()
    assert (
        "Cached owner/project metadata is incomplete;" in notices[0].getMessage()
    ) == (not owner or not project)

    other_client, _ = make_client(RunClient, log_context=True)
    assert other_client.run_uuid == CACHED_UUID
    assert caplog.text.count("Using cached run") == 2


def test_explicit_uuid_overrides_conflicting_cache(cache_run, make_client, caplog):
    cache_run()
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    client, sdk = make_client(
        RunClient,
        owner=None,
        project=None,
        log_context=True,
        run_uuid=NEW_UUID,
    )
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    assert client.get_namespace() == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(OWNER, PROJECT, NEW_UUID)
    fields, _ = _get_client_context(client, include_run=True)
    assert fields[-1][1] == NEW_UUID
    assert fields[-1][2].path is None
    assert "Using cached run" not in caplog.text
    assert caplog.text.count("Using cached project") == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
async def test_list_does_not_consume_cached_run(
    client_type, cache_run, make_client, caplog
):
    cache_run()
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    client, sdk = make_client(client_type, owner=None, project=None, log_context=True)
    assert caplog.text.count("Using cached project") == 1
    response = SimpleNamespace(results=[])
    sdk.runs_v1.list_runs.return_value = response

    assert await call_client(client.list) is response
    assert sdk.runs_v1.list_runs.call_args.args == (OWNER, PROJECT)
    with pytest.raises(PolyaxonClientException):
        _ = client.run_uuid
    assert "Using cached run" not in caplog.text
    assert caplog.text.count("Using cached project") == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", CLIENT_TYPES)
async def test_create_replaces_conflicting_cached_run(
    client_type, cache_run, make_client, caplog
):
    cache_run()
    client, sdk = make_client(client_type)
    created = V1Run(uuid=NEW_UUID, owner=OWNER, project=PROJECT)
    sdk.runs_v1.create_run.return_value = created
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    assert await call_client(client.create, name="new-run") is created
    assert client.run_uuid == NEW_UUID
    fields, _ = _get_client_context(client, include_run=True)
    assert fields[-1][1] == NEW_UUID
    assert fields[-1][2].path is None
    assert sdk.runs_v1.create_run.call_args.kwargs["project"] == PROJECT
    assert await call_client(client.get_namespace) == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(OWNER, PROJECT, NEW_UUID)
    assert "Using cached run" not in caplog.text


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


def test_set_run_uuid_replaces_conflicting_cache(cache_run, make_client):
    cache_run()
    client, _ = make_client(RunClient)

    client.set_run_uuid(NEW_UUID)

    assert client.run_uuid == NEW_UUID
    fields, _ = _get_client_context(client, include_run=True)
    assert fields[-1][1] == NEW_UUID
    assert fields[-1][2].path is None


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
async def test_successful_transfer_releases_cached_project_identity(
    client_type, cache_run, make_client
):
    cache_run(project=PROJECT)
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    client, sdk = make_client(client_type, owner=None, project=None)
    sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

    await call_client(client.transfer, CACHED_PROJECT)

    assert client.project == CACHED_PROJECT
    assert client.run_data.project == CACHED_PROJECT
    assert client.run_uuid == CACHED_UUID
    fields, _ = _get_client_context(client, include_run=True)
    assert fields[1][1] == CACHED_PROJECT
    assert fields[1][2].kind == "explicit"
    assert fields[1][2].path is None
    assert fields[-1][1] == CACHED_UUID
    assert fields[-1][2].path is None
    assert await call_client(client.get_namespace) == "ns"
    sdk.runs_v1.get_run_namespace.assert_called_once_with(
        OWNER, CACHED_PROJECT, CACHED_UUID
    )

    await call_client(client.transfer, PROJECT)

    fields, _ = _get_client_context(client)
    assert fields[1][1] == PROJECT
    assert fields[1][2].kind == "explicit"
    assert fields[1][2].path is None


@pytest.mark.asyncio
@pytest.mark.parametrize("client_type", RUN_CLIENT_TYPES)
async def test_failed_transfer_keeps_cached_project_identity(
    client_type, cache_run, make_client
):
    cache_run(project=PROJECT)
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    cache_path = str(
        Path(ProjectConfigManager.get_config_filepath(create=False)).resolve()
    )
    client, sdk = make_client(client_type, owner=None, project=None)
    sdk.runs_v1.transfer_run.side_effect = RuntimeError("transfer failed")

    with pytest.raises(RuntimeError, match="transfer failed"):
        await call_client(client.transfer, CACHED_PROJECT)

    assert client.project == PROJECT
    assert client.run_uuid == CACHED_UUID
    fields, _ = _get_client_context(client)
    assert fields[1][2].kind == "local cache"
    assert fields[1][2].path == cache_path
    client.set_project(CACHED_PROJECT)
    with pytest.raises(PolyaxonClientException):
        _ = client.run_uuid


def test_offline_run_does_not_reuse_cached_uuid(cache_run, make_client, caplog):
    cache_run()
    client, sdk = make_client(RunClient, is_offline=True)

    fields, incomplete_run = _get_client_context(client, include_run=True)
    assert [name for name, _, _ in fields] == ["Owner", "Project"]
    assert incomplete_run is False
    assert client.run_uuid
    assert client.run_uuid != CACHED_UUID
    assert client.get_namespace() is None
    sdk.runs_v1.get_run_namespace.assert_not_called()
    assert "Using cached run" not in caplog.text


def test_offline_sandbox_preserves_cached_uuid(cache_run, make_client, caplog):
    cache_run()
    client, sdk = make_client(SandboxClient, is_offline=True)

    fields, incomplete_run = _get_client_context(client, include_run=True)
    assert [name for name, _, _ in fields] == ["Owner", "Project"]
    assert incomplete_run is False
    assert client.run_uuid == CACHED_UUID
    assert client.get_namespace() is None
    sdk.runs_v1.get_run_namespace.assert_not_called()
    assert "Using cached run" not in caplog.text


def test_no_op_does_not_consume_cached_context(cache_run, make_client, caplog):
    cache_run()
    client, sdk = make_client(RunClient, no_op=True)

    assert _get_client_context(client, include_run=True) is None
    assert client.get_namespace() is None
    sdk.runs_v1.get_run_namespace.assert_not_called()
    assert "Using cached run" not in caplog.text


def test_global_no_op_skips_context_snapshot(cache_run, make_client, caplog):
    cache_run()
    settings.CLIENT_CONFIG.no_op = True
    client, _ = make_client(RunClient, log_context=True)

    assert _get_client_context(client, include_run=True) is None
    assert "Using cached" not in caplog.text


def test_managed_run_identity_does_not_reuse_cached_uuid(
    cache_run, make_client, monkeypatch, caplog
):
    cache_run()
    settings.CLIENT_CONFIG.is_managed = True
    monkeypatch.setenv(ENV_KEYS_RUN_INSTANCE, f"{OWNER}.{PROJECT}.runs.{NEW_UUID}")

    client, _ = make_client(RunClient, owner=None, project=None, log_context=True)

    assert (client.owner, client.project, client.run_uuid) == (
        OWNER,
        PROJECT,
        NEW_UUID,
    )
    fields, _ = _get_client_context(client, include_run=True)
    assert [(name, value) for name, value, _ in fields[:2]] == [
        ("Owner", OWNER),
        ("Project", PROJECT),
    ]
    assert fields[-1][1] == NEW_UUID
    assert fields[-1][2].path is None
    assert "Using cached run" not in caplog.text


@pytest.mark.parametrize(
    "visibility,cached_project",
    [
        pytest.param("local", PROJECT, id="complete-local"),
        pytest.param("global", None, id="incomplete-global"),
    ],
)
@pytest.mark.parametrize("client_type", CONTEXT_CLIENT_TYPES)
def test_context_snapshot_does_not_consume_run_notice(
    client_type, visibility, cached_project, cache_run, make_client, caplog
):
    cache_path = cache_run(project=cached_project, visibility=visibility)
    client, _ = make_client(client_type, log_context=True)

    fields, incomplete_run = _get_client_context(client, include_run=True)

    assert fields[-1][1] == CACHED_UUID
    assert fields[-1][2].kind == f"{visibility} cache"
    assert fields[-1][2].path == cache_path
    assert incomplete_run is (cached_project is None)
    assert "Using cached" not in caplog.text

    _get_client_context(client, include_run=True)
    assert "Using cached" not in caplog.text

    assert client.run_uuid == CACHED_UUID
    assert client.run_uuid == CACHED_UUID
    assert caplog.text.count("Using cached run") == 1


def test_notice_handler_can_read_run_uuid(cache_run, make_client, monkeypatch):
    cache_run(project=PROJECT)
    client, _ = make_client(RunClient, log_context=True)
    log_info = MagicMock(side_effect=lambda message: client.run_uuid)
    monkeypatch.setattr("polyaxon.logger.logger.info", log_info)

    assert client.run_uuid == CACHED_UUID
    log_info.assert_called_once()


@pytest.mark.parametrize("client_type", CONTEXT_CLIENT_TYPES)
def test_reported_cache_is_still_validated(client_type, cache_run, make_client, caplog):
    cache_run(project=PROJECT)
    client, _ = make_client(client_type, log_context=True)

    assert client.run_uuid == CACHED_UUID
    client.set_project(CACHED_PROJECT)
    fields, incomplete_run = _get_client_context(client)
    assert fields[1][1] == CACHED_PROJECT
    assert incomplete_run is False
    with pytest.raises(PolyaxonClientException):
        _get_client_context(client, include_run=True)
    with pytest.raises(PolyaxonClientException):
        _ = client.run_uuid
    assert caplog.text.count("Using cached run") == 1


def test_context_logging_defaults_to_quiet(cache_run, make_client, caplog, capsys):
    cache_run(project=PROJECT)
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    client, _ = make_client(RunClient, owner=None, project=None)

    assert client.log_context is False
    assert client.run_uuid == CACHED_UUID
    assert client.run_uuid == CACHED_UUID
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert "Using cached" not in caplog.text


def test_context_logging_can_be_enabled_per_instance(cache_run, make_client, caplog):
    cache_run(project=PROJECT)
    client, _ = make_client(RunClient)
    other_client, _ = make_client(RunClient)

    assert client.run_uuid == other_client.run_uuid == CACHED_UUID
    assert "Using cached run" not in caplog.text

    client.log_context = True
    assert client.run_uuid == CACHED_UUID
    assert client.run_uuid == CACHED_UUID
    assert other_client.run_uuid == CACHED_UUID
    assert caplog.text.count("Using cached run") == 1
    assert other_client.log_context is False

    client.log_context = False
    client.set_project(CACHED_PROJECT)
    with pytest.raises(PolyaxonClientException):
        _ = client.run_uuid
    assert caplog.text.count("Using cached run") == 1


@pytest.mark.parametrize("project_visibility", [None, "local", "global"])
def test_context_logging_keeps_conflicts_as_client_exceptions(
    project_visibility, cache_run, make_client, caplog
):
    run_path = cache_run()
    kwargs = {}
    if project_visibility:
        ProjectConfigManager.set_config(
            V1Project(owner=OWNER, name=PROJECT), visibility=project_visibility
        )
        project_path = str(
            Path(ProjectConfigManager.get_config_filepath(create=False)).resolve()
        )
        kwargs.update(owner=None, project=None)
    client, _ = make_client(RunClient, log_context=True, **kwargs)

    with pytest.raises(PolyaxonClientException) as report_error:
        _get_client_context(client, include_run=True)
    with pytest.raises(PolyaxonClientException) as uuid_error:
        _ = client.run_uuid

    message = str(report_error.value)
    assert message == str(uuid_error.value)
    assert f"local cache · {run_path}" in message
    if project_visibility:
        assert f"owner: {project_visibility} cache · {project_path}" in message
        assert f"project: {project_visibility} cache · {project_path}" in message
    else:
        assert "owner: explicit; project: explicit" in message

    assert "Using cached run" not in caplog.text


def test_cached_run_without_uuid_is_ignored(make_client, caplog):
    RunConfigManager.set_config(V1Run(owner=OWNER, project=PROJECT), visibility="local")
    client, _ = make_client(RunClient, log_context=True)

    assert client.run_uuid is None
    assert "Using cached run" not in caplog.text


def test_initializer_client_defaults_to_quiet(cache_run, caplog, capsys):
    from polyaxon._client.init import get_client_or_raise

    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    cache_run(project=PROJECT)
    client = get_client_or_raise()

    assert client.log_context is False
    assert client.run_uuid == CACHED_UUID
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert "Using cached" not in caplog.text


@pytest.mark.parametrize(
    "field,initial",
    [("owner", OWNER), ("project", PROJECT)],
)
def test_context_setters_mark_same_value_explicit(
    field, initial, cache_run, make_client
):
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    project_path = str(
        Path(ProjectConfigManager.get_config_filepath(create=False)).resolve()
    )
    run_path = cache_run(project=PROJECT)
    client, _ = make_client(RunClient, owner=None, project=None)
    setter = getattr(client, f"set_{field}")

    setter(initial)

    fields, _ = _get_client_context(client, include_run=True)
    changed = fields[0 if field == "owner" else 1]
    unchanged = fields[1 if field == "owner" else 0]
    assert changed[1] == initial
    assert changed[2].kind == "explicit"
    assert changed[2].path is None
    assert unchanged[2].kind == "local cache"
    assert unchanged[2].path == project_path
    assert fields[-1][2].path == run_path
    assert client.run_uuid == CACHED_UUID


@pytest.mark.parametrize(
    "field,initial,replacement",
    [("owner", OWNER, "other-owner"), ("project", PROJECT, CACHED_PROJECT)],
)
def test_context_setters_keep_explicit_provenance_after_round_trip(
    field, initial, replacement, cache_run, make_client
):
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=PROJECT), visibility="local"
    )
    project_path = str(
        Path(ProjectConfigManager.get_config_filepath(create=False)).resolve()
    )
    run_path = cache_run(project=PROJECT)
    client, _ = make_client(RunClient, owner=None, project=None)
    setter = getattr(client, f"set_{field}")

    setter(replacement)
    with pytest.raises(PolyaxonClientException) as error:
        _ = client.run_uuid
    assert f"{field}: explicit" in str(error.value)

    setter(initial)

    fields, _ = _get_client_context(client, include_run=True)
    changed = fields[0 if field == "owner" else 1]
    unchanged = fields[1 if field == "owner" else 0]
    assert changed[1] == initial
    assert changed[2].kind == "explicit"
    assert changed[2].path is None
    assert unchanged[2].kind == "local cache"
    assert unchanged[2].path == project_path
    assert fields[-1][2].path == run_path
    assert client.run_uuid == CACHED_UUID


def test_owner_setter_updates_team_and_provenance(make_client):
    ProjectConfigManager.set_config(
        V1Project(owner=f"{OWNER}/old-team", name=PROJECT), visibility="local"
    )
    client, _ = make_client(RunClient, owner=None, project=None, run_uuid=NEW_UUID)

    client.set_owner(f"{OWNER}/new-team")

    fields, _ = _get_client_context(client)
    assert client.team == "new-team"
    assert fields[0][1] == f"{OWNER}/new-team"
    assert fields[0][2].kind == "explicit"
    assert fields[0][2].path is None
    assert fields[1][2].kind == "local cache"

    client.set_owner(OWNER)

    fields, _ = _get_client_context(client)
    assert client.team is None
    assert fields[0][1] == OWNER
    assert fields[0][2].kind == "explicit"
    assert fields[0][2].path is None


@pytest.mark.parametrize("reset_project", [False, True])
def test_loading_offline_run_replaces_cached_identity(
    reset_project, cache_run, make_client, tmp_path
):
    cache_run()
    ProjectConfigManager.set_config(
        V1Project(owner=OWNER, name=CACHED_PROJECT), visibility="local"
    )
    client, _ = make_client(RunClient, owner=None, project=None)
    original_fields, _ = _get_client_context(client)
    persisted = V1Run(uuid=NEW_UUID, owner="other-owner", project=PROJECT)
    (tmp_path / ctx_paths.CONTEXT_LOCAL_RUN).write_text(persisted.to_json())

    restored = RunClient.load_offline_run(
        path=str(tmp_path), run_client=client, reset_project=reset_project
    )

    assert restored is client
    assert client.run_uuid == NEW_UUID
    fields, _ = _get_client_context(client, include_run=True)
    assert fields[-1][1] == NEW_UUID
    assert fields[-1][2].kind == "explicit"
    assert fields[-1][2].path is None
    if reset_project:
        assert (client.owner, client.project) == (OWNER, CACHED_PROJECT)
        assert fields[:2] == original_fields
    else:
        assert (client.owner, client.project) == ("other-owner", PROJECT)
        assert fields[0][1] == "other-owner"
        assert fields[1][1] == PROJECT
        assert all(source.kind == "explicit" for _, _, source in fields)
        assert all(source.path is None for _, _, source in fields)


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
