import inspect
from io import StringIO
import os
from pathlib import Path
import pytest
import tempfile
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from polyaxon import settings
from polyaxon._cli.context import _get_client_context
from polyaxon._client.run import AsyncRunClient, RunClient
from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import ENV_KEYS_RUN_INSTANCE
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_user import V1User
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError


OWNER = "owner"
PROJECT = "project-b"
CACHED_PROJECT = "project-a"
CACHED_UUID = "11111111111111111111111111111111"
NEW_UUID = "22222222222222222222222222222222"
CLIENT_TYPES = (RunClient, AsyncRunClient, SandboxClient, AsyncSandboxClient)
CONTEXT_CLIENT_TYPES = (RunClient, SandboxClient)
RUN_CLIENT_TYPES = (RunClient, AsyncRunClient)


@pytest.mark.client_mark
class TestCachedRunContext(BaseTestCase, IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        local_cache = str(self.directory / "local" / ".polyaxon")
        global_cache = str(self.directory / "global" / ".polyaxon")
        for patcher in (
            patch.object(ctx_paths, "CONTEXT_USER_POLYAXON_PATH", global_cache),
            patch.dict(os.environ),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        for manager in (ProjectConfigManager, RunConfigManager, UserConfigManager):
            patcher = patch.multiple(
                manager,
                CONFIG_PATH=None,
                _PROJECT=local_cache,
                _PROJECT_PATH=global_cache,
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        super().setUp()
        os.environ.pop(ENV_KEYS_RUN_INSTANCE, None)

    def cache_project(self, owner=OWNER, project=PROJECT, visibility="local"):
        ProjectConfigManager.set_config(
            V1Project(owner=owner, name=project), visibility=visibility
        )
        return os.path.abspath(ProjectConfigManager.get_config_filepath(create=False))

    def cache_run(self, owner=OWNER, project=CACHED_PROJECT, visibility="local"):
        RunConfigManager.set_config(
            V1Run(uuid=CACHED_UUID, owner=owner, project=project),
            visibility=visibility,
        )
        return os.path.abspath(RunConfigManager.get_config_filepath(create=False))

    def make_client(self, client_type, **kwargs):
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

    @staticmethod
    async def call_client(method, *args, **kwargs):
        response = method(*args, **kwargs)
        if inspect.isawaitable(response):
            return await response
        return response

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    def test_cached_project_logging_can_be_disabled(self, log_info, stdout, stderr):
        self.cache_project()
        for client_type in CONTEXT_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client, _ = self.make_client(
                    client_type,
                    owner=None,
                    project=None,
                    run_uuid=NEW_UUID,
                    log_context=False,
                )

                assert (client.owner, client.project, client.run_uuid) == (
                    OWNER,
                    PROJECT,
                    NEW_UUID,
                )
                assert client.team is None
                fields, _ = _get_client_context(client)
                assert fields[0][1] == OWNER

        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_local_project_logging_includes_team(self, stdout, stderr):
        owner = f"{OWNER}/team"
        cache_path = self.cache_project(owner=owner)
        for client_type in CONTEXT_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client, _ = self.make_client(
                        client_type,
                        owner=None,
                        project=None,
                        run_uuid=NEW_UUID,
                        log_context=True,
                    )

                    assert (client.owner, client.project, client.run_uuid) == (
                        OWNER,
                        PROJECT,
                        NEW_UUID,
                    )
                    assert client.team == "team"
                    fields, _ = _get_client_context(client)
                    assert fields[0][1] == owner

                assert logs.output == [
                    f"INFO:polyaxon.cli:Using cached project `{owner}/{PROJECT}` "
                    f"from `{cache_path}`."
                ]

        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_global_project_logging_uses_global_source(self, stdout, stderr):
        cache_path = self.cache_project(visibility="global")
        for client_type in CONTEXT_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client, _ = self.make_client(
                        client_type,
                        owner=None,
                        project=None,
                        run_uuid=NEW_UUID,
                        log_context=True,
                    )

                    assert (client.owner, client.project, client.run_uuid) == (
                        OWNER,
                        PROJECT,
                        NEW_UUID,
                    )
                    assert client.team is None
                    fields, _ = _get_client_context(client)
                    assert fields[0][1] == OWNER

                assert logs.output == [
                    f"INFO:polyaxon.cli:Using cached project `{OWNER}/{PROJECT}` "
                    f"from `{cache_path}`."
                ]

        assert stdout.getvalue() == stderr.getvalue() == ""

    def test_explicit_project_team_is_preserved(self):
        client, _ = self.make_client(
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

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_cached_owner_logging_with_explicit_project(self, stdout, stderr):
        UserConfigManager.set_config(V1User(organization=OWNER))
        owner_path = os.path.abspath(
            UserConfigManager.get_config_filepath(create=False)
        )

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, _ = self.make_client(
                RunClient,
                owner=None,
                project=PROJECT,
                run_uuid=NEW_UUID,
                log_context=True,
            )

            assert (client.owner, client.project, client.run_uuid) == (
                OWNER,
                PROJECT,
                NEW_UUID,
            )

        assert logs.output == [
            f"INFO:polyaxon.cli:Using cached owner `{OWNER}` from `{owner_path}`."
        ]
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_cached_owner_and_project_keep_separate_sources(self, stdout, stderr):
        UserConfigManager.set_config(V1User(organization=OWNER))
        owner_path = os.path.abspath(
            UserConfigManager.get_config_filepath(create=False)
        )
        project_path = self.cache_project(owner=None)

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, _ = self.make_client(
                RunClient,
                owner=None,
                project=None,
                run_uuid=NEW_UUID,
                log_context=True,
            )

            assert (client.owner, client.project, client.run_uuid) == (
                OWNER,
                PROJECT,
                NEW_UUID,
            )

        assert logs.output == [
            f"INFO:polyaxon.cli:Using cached owner `{OWNER}` from `{owner_path}`.",
            f"INFO:polyaxon.cli:Using cached project `{PROJECT}` "
            f"from `{project_path}`.",
        ]
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    def test_context_logging_keeps_invalid_projects_as_schema_errors(
        self, log_info, stdout, stderr
    ):
        with self.assertRaisesRegex(PolyaxonSchemaError, "invalid project"):
            self.make_client(RunClient, project="invalid project", log_context=True)

        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_cached_project_mismatch_rejected_before_run_request(
        self, log_info, log_warning
    ):
        cache_path = self.cache_run()
        client, sdk = self.make_client(RunClient, log_context=True)

        assert client.run_data.uuid == CACHED_UUID
        with self.assertRaises(PolyaxonClientException) as error:
            client.get_namespace()

        message = str(error.exception)
        assert f"{OWNER}/{PROJECT}" in message
        assert f"{OWNER}/{CACHED_PROJECT}" in message
        assert f"local cache · {cache_path}" in message
        assert "owner: explicit; project: explicit" in message
        sdk.runs_v1.get_run_namespace.assert_not_called()
        log_info.assert_not_called()
        log_warning.assert_not_called()

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_cached_owner_mismatch_rejected_before_run_request(
        self, log_info, log_warning
    ):
        cache_path = self.cache_run(owner="other-owner", project=PROJECT)
        client, sdk = self.make_client(RunClient, log_context=True)

        assert client.run_data.uuid == CACHED_UUID
        with self.assertRaises(PolyaxonClientException) as error:
            client.get_namespace()

        message = str(error.exception)
        assert f"{OWNER}/{PROJECT}" in message
        assert f"other-owner/{PROJECT}" in message
        assert f"local cache · {cache_path}" in message
        assert "owner: explicit; project: explicit" in message
        sdk.runs_v1.get_run_namespace.assert_not_called()
        log_info.assert_not_called()
        log_warning.assert_not_called()

    async def test_cached_mismatch_rejected_across_client_types(self):
        self.cache_run()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client, sdk = self.make_client(client_type)

                with self.assertRaises(PolyaxonClientException):
                    await self.call_client(client.get_namespace)

                sdk.runs_v1.get_run_namespace.assert_not_called()

    def test_local_project_does_not_accept_unrelated_global_run(self):
        self.cache_run(visibility="global")
        self.cache_project()
        client, sdk = self.make_client(RunClient, owner=None, project=None)

        assert (client.owner, client.project) == (OWNER, PROJECT)
        with self.assertRaises(PolyaxonClientException):
            client.get_namespace()

        sdk.runs_v1.get_run_namespace.assert_not_called()

    def test_matching_cached_run_is_reported_once_per_client(self):
        cache_path = self.cache_run(project=PROJECT)
        notice = (
            f"INFO:polyaxon.cli:Using cached run `{CACHED_UUID}` from `{cache_path}`."
        )

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, sdk = self.make_client(RunClient, log_context=True)
            sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

            assert logs.output == []
            assert client.get_namespace() == "ns"
            sdk.runs_v1.get_run_namespace.assert_called_once_with(
                OWNER, PROJECT, CACHED_UUID
            )
            assert client.run_uuid == CACHED_UUID
            assert logs.output == [notice]

            other_client, _ = self.make_client(RunClient, log_context=True)
            assert other_client.run_uuid == CACHED_UUID

        assert logs.output == [notice, notice]

    def test_incomplete_cached_run_warns_once_per_client(self):
        cache_path = self.cache_run(project=None)
        notice = (
            f"WARNING:polyaxon.cli:Using cached run `{CACHED_UUID}` "
            f"from `{cache_path}`. "
            "Cached owner/project metadata is incomplete; "
            "only known ownership fields were checked."
        )

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, sdk = self.make_client(RunClient, log_context=True)
            sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

            assert logs.output == []
            assert client.get_namespace() == "ns"
            sdk.runs_v1.get_run_namespace.assert_called_once_with(
                OWNER, PROJECT, CACHED_UUID
            )
            assert client.run_uuid == CACHED_UUID
            assert logs.output == [notice]

            other_client, _ = self.make_client(RunClient, log_context=True)
            assert other_client.run_uuid == CACHED_UUID

        assert logs.output == [notice, notice]

    def test_explicit_uuid_overrides_conflicting_cache(self):
        self.cache_run()
        project_path = self.cache_project()

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, sdk = self.make_client(
                RunClient,
                owner=None,
                project=None,
                log_context=True,
                run_uuid=NEW_UUID,
            )
            sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(namespace="ns")

            assert client.get_namespace() == "ns"
            sdk.runs_v1.get_run_namespace.assert_called_once_with(
                OWNER, PROJECT, NEW_UUID
            )
            fields, _ = _get_client_context(client, include_run=True)
            assert fields[-1][1] == NEW_UUID
            assert fields[-1][2].path is None

        assert logs.output == [
            f"INFO:polyaxon.cli:Using cached project `{OWNER}/{PROJECT}` "
            f"from `{project_path}`."
        ]

    async def test_list_does_not_consume_cached_run(self):
        self.cache_run()
        project_path = self.cache_project()
        notice = (
            f"INFO:polyaxon.cli:Using cached project `{OWNER}/{PROJECT}` "
            f"from `{project_path}`."
        )
        for client_type in RUN_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client, sdk = self.make_client(
                        client_type, owner=None, project=None, log_context=True
                    )
                    assert logs.output == [notice]
                    response = SimpleNamespace(results=[])
                    sdk.runs_v1.list_runs.return_value = response

                    assert await self.call_client(client.list) is response
                    assert sdk.runs_v1.list_runs.call_args.args == (OWNER, PROJECT)
                    with self.assertRaises(PolyaxonClientException):
                        _ = client.run_uuid

                assert logs.output == [notice]

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    async def test_create_replaces_conflicting_cached_run(self, log_info, log_warning):
        self.cache_run()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client, sdk = self.make_client(client_type)
                created = V1Run(uuid=NEW_UUID, owner=OWNER, project=PROJECT)
                sdk.runs_v1.create_run.return_value = created
                sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(
                    namespace="ns"
                )

                assert await self.call_client(client.create, name="new-run") is created
                assert client.run_uuid == NEW_UUID
                fields, _ = _get_client_context(client, include_run=True)
                assert fields[-1][1] == NEW_UUID
                assert fields[-1][2].path is None
                assert sdk.runs_v1.create_run.call_args.kwargs["project"] == PROJECT
                assert await self.call_client(client.get_namespace) == "ns"
                sdk.runs_v1.get_run_namespace.assert_called_once_with(
                    OWNER, PROJECT, NEW_UUID
                )

        log_info.assert_not_called()
        log_warning.assert_not_called()

    async def test_failed_creation_preserves_cached_conflict(self):
        self.cache_run()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client, sdk = self.make_client(client_type)
                sdk.runs_v1.create_run.side_effect = RuntimeError("creation failed")

                with self.assertRaisesRegex(RuntimeError, "creation failed"):
                    await self.call_client(client.create)

                assert client.run_data.uuid == CACHED_UUID
                with self.assertRaises(PolyaxonClientException):
                    await self.call_client(client.get_namespace)

                sdk.runs_v1.get_run_namespace.assert_not_called()

    def test_set_run_uuid_replaces_conflicting_cache(self):
        self.cache_run()
        client, _ = self.make_client(RunClient)

        client.set_run_uuid(NEW_UUID)

        assert client.run_uuid == NEW_UUID
        fields, _ = _get_client_context(client, include_run=True)
        assert fields[-1][1] == NEW_UUID
        assert fields[-1][2].path is None

    async def test_successful_transfer_releases_cached_project_identity(self):
        self.cache_run(project=PROJECT)
        self.cache_project()
        for client_type in RUN_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client, sdk = self.make_client(client_type, owner=None, project=None)
                sdk.runs_v1.get_run_namespace.return_value = SimpleNamespace(
                    namespace="ns"
                )

                await self.call_client(client.transfer, CACHED_PROJECT)

                assert client.project == CACHED_PROJECT
                assert client.run_data.project == CACHED_PROJECT
                assert client.run_uuid == CACHED_UUID
                fields, _ = _get_client_context(client, include_run=True)
                assert fields[1][1] == CACHED_PROJECT
                assert fields[1][2].kind == "explicit"
                assert fields[1][2].path is None
                assert fields[-1][1] == CACHED_UUID
                assert fields[-1][2].path is None
                assert await self.call_client(client.get_namespace) == "ns"
                sdk.runs_v1.get_run_namespace.assert_called_once_with(
                    OWNER, CACHED_PROJECT, CACHED_UUID
                )

                await self.call_client(client.transfer, PROJECT)

                fields, _ = _get_client_context(client)
                assert fields[1][1] == PROJECT
                assert fields[1][2].kind == "explicit"
                assert fields[1][2].path is None

    async def test_failed_transfer_keeps_cached_project_identity(self):
        self.cache_run(project=PROJECT)
        cache_path = self.cache_project()
        for client_type in RUN_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client, sdk = self.make_client(client_type, owner=None, project=None)
                sdk.runs_v1.transfer_run.side_effect = RuntimeError("transfer failed")

                with self.assertRaisesRegex(RuntimeError, "transfer failed"):
                    await self.call_client(client.transfer, CACHED_PROJECT)

                assert client.project == PROJECT
                assert client.run_uuid == CACHED_UUID
                fields, _ = _get_client_context(client)
                assert fields[1][2].kind == "local cache"
                assert fields[1][2].path == cache_path
                client.set_project(CACHED_PROJECT)
                with self.assertRaises(PolyaxonClientException):
                    _ = client.run_uuid

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_offline_run_does_not_reuse_cached_uuid(self, log_info, log_warning):
        self.cache_run()
        client, sdk = self.make_client(RunClient, is_offline=True)

        fields, incomplete_run = _get_client_context(client, include_run=True)
        assert [name for name, _, _ in fields] == ["Owner", "Project"]
        assert incomplete_run is False
        assert client.run_uuid
        assert client.run_uuid != CACHED_UUID
        assert client.get_namespace() is None
        sdk.runs_v1.get_run_namespace.assert_not_called()
        log_info.assert_not_called()
        log_warning.assert_not_called()

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_offline_sandbox_preserves_cached_uuid(self, log_info, log_warning):
        self.cache_run()
        client, sdk = self.make_client(SandboxClient, is_offline=True)

        fields, incomplete_run = _get_client_context(client, include_run=True)
        assert [name for name, _, _ in fields] == ["Owner", "Project"]
        assert incomplete_run is False
        assert client.run_uuid == CACHED_UUID
        assert client.get_namespace() is None
        sdk.runs_v1.get_run_namespace.assert_not_called()
        log_info.assert_not_called()
        log_warning.assert_not_called()

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_no_op_does_not_consume_cached_context(self, log_info, log_warning):
        self.cache_run()
        client, sdk = self.make_client(RunClient, no_op=True)

        assert _get_client_context(client, include_run=True) is None
        assert client.get_namespace() is None
        sdk.runs_v1.get_run_namespace.assert_not_called()
        log_info.assert_not_called()
        log_warning.assert_not_called()

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_global_no_op_skips_context_snapshot(self, log_info, log_warning):
        self.cache_run()
        settings.CLIENT_CONFIG.no_op = True
        client, _ = self.make_client(RunClient, log_context=True)

        assert _get_client_context(client, include_run=True) is None
        log_info.assert_not_called()
        log_warning.assert_not_called()

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_managed_run_identity_does_not_reuse_cached_uuid(
        self, log_info, log_warning
    ):
        self.cache_run()
        settings.CLIENT_CONFIG.is_managed = True
        os.environ[ENV_KEYS_RUN_INSTANCE] = f"{OWNER}.{PROJECT}.runs.{NEW_UUID}"

        client, _ = self.make_client(
            RunClient, owner=None, project=None, log_context=True
        )

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
        log_info.assert_not_called()
        log_warning.assert_not_called()

    def test_local_context_snapshot_does_not_consume_run_notice(self):
        cache_path = self.cache_run(project=PROJECT)
        for client_type in CONTEXT_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client, _ = self.make_client(client_type, log_context=True)
                    fields, incomplete_run = _get_client_context(
                        client, include_run=True
                    )

                    assert fields[-1][1] == CACHED_UUID
                    assert fields[-1][2].kind == "local cache"
                    assert fields[-1][2].path == cache_path
                    assert incomplete_run is False
                    assert logs.output == []

                    _get_client_context(client, include_run=True)
                    assert logs.output == []
                    assert client.run_uuid == CACHED_UUID
                    assert client.run_uuid == CACHED_UUID

                assert logs.output == [
                    f"INFO:polyaxon.cli:Using cached run `{CACHED_UUID}` "
                    f"from `{cache_path}`."
                ]

    def test_incomplete_global_snapshot_does_not_consume_run_warning(self):
        cache_path = self.cache_run(project=None, visibility="global")
        for client_type in CONTEXT_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client, _ = self.make_client(client_type, log_context=True)
                    fields, incomplete_run = _get_client_context(
                        client, include_run=True
                    )

                    assert fields[-1][1] == CACHED_UUID
                    assert fields[-1][2].kind == "global cache"
                    assert fields[-1][2].path == cache_path
                    assert incomplete_run is True
                    assert logs.output == []

                    _get_client_context(client, include_run=True)
                    assert logs.output == []
                    assert client.run_uuid == CACHED_UUID
                    assert client.run_uuid == CACHED_UUID

                assert logs.output == [
                    f"WARNING:polyaxon.cli:Using cached run `{CACHED_UUID}` "
                    f"from `{cache_path}`. "
                    "Cached owner/project metadata is incomplete; "
                    "only known ownership fields were checked."
                ]

    @patch("polyaxon.logger.logger.info")
    def test_notice_handler_can_read_run_uuid(self, log_info):
        self.cache_run(project=PROJECT)
        client, _ = self.make_client(RunClient, log_context=True)
        log_info.side_effect = lambda message: client.run_uuid

        assert client.run_uuid == CACHED_UUID
        log_info.assert_called_once()

    def test_reported_cache_is_still_validated(self):
        cache_path = self.cache_run(project=PROJECT)
        for client_type in CONTEXT_CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client, _ = self.make_client(client_type, log_context=True)

                    assert client.run_uuid == CACHED_UUID
                    client.set_project(CACHED_PROJECT)
                    fields, incomplete_run = _get_client_context(client)
                    assert fields[1][1] == CACHED_PROJECT
                    assert incomplete_run is False
                    with self.assertRaises(PolyaxonClientException):
                        _get_client_context(client, include_run=True)
                    with self.assertRaises(PolyaxonClientException):
                        _ = client.run_uuid

                assert logs.output == [
                    f"INFO:polyaxon.cli:Using cached run `{CACHED_UUID}` "
                    f"from `{cache_path}`."
                ]

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_context_logging_defaults_to_quiet(
        self, log_info, log_warning, stdout, stderr
    ):
        self.cache_run(project=PROJECT)
        self.cache_project()
        client, _ = self.make_client(RunClient, owner=None, project=None)

        assert client.log_context is False
        assert client.run_uuid == CACHED_UUID
        assert client.run_uuid == CACHED_UUID
        log_info.assert_not_called()
        log_warning.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    def test_context_logging_can_be_enabled_per_instance(self):
        cache_path = self.cache_run(project=PROJECT)
        notice = (
            f"INFO:polyaxon.cli:Using cached run `{CACHED_UUID}` from `{cache_path}`."
        )

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, _ = self.make_client(RunClient)
            other_client, _ = self.make_client(RunClient)

            assert client.run_uuid == other_client.run_uuid == CACHED_UUID
            assert logs.output == []

            client.log_context = True
            assert client.run_uuid == CACHED_UUID
            assert client.run_uuid == CACHED_UUID
            assert other_client.run_uuid == CACHED_UUID
            assert logs.output == [notice]
            assert other_client.log_context is False

            client.log_context = False
            client.set_project(CACHED_PROJECT)
            with self.assertRaises(PolyaxonClientException):
                _ = client.run_uuid

        assert logs.output == [notice]

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_explicit_project_conflicts_remain_client_exceptions(
        self, log_info, log_warning
    ):
        run_path = self.cache_run()
        client, _ = self.make_client(RunClient, log_context=True)

        with self.assertRaises(PolyaxonClientException) as report_error:
            _get_client_context(client, include_run=True)
        with self.assertRaises(PolyaxonClientException) as uuid_error:
            _ = client.run_uuid

        message = str(report_error.exception)
        assert message == str(uuid_error.exception)
        assert f"local cache · {run_path}" in message
        assert "owner: explicit; project: explicit" in message
        log_info.assert_not_called()
        log_warning.assert_not_called()

    def test_local_project_conflicts_remain_client_exceptions(self):
        run_path = self.cache_run()
        project_path = self.cache_project()

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, _ = self.make_client(
                RunClient, owner=None, project=None, log_context=True
            )

            with self.assertRaises(PolyaxonClientException) as report_error:
                _get_client_context(client, include_run=True)
            with self.assertRaises(PolyaxonClientException) as uuid_error:
                _ = client.run_uuid

        message = str(report_error.exception)
        assert message == str(uuid_error.exception)
        assert f"local cache · {run_path}" in message
        assert f"owner: local cache · {project_path}" in message
        assert f"project: local cache · {project_path}" in message
        assert logs.output == [
            f"INFO:polyaxon.cli:Using cached project `{OWNER}/{PROJECT}` "
            f"from `{project_path}`."
        ]

    def test_global_project_conflicts_remain_client_exceptions(self):
        run_path = self.cache_run()
        project_path = self.cache_project(visibility="global")

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            client, _ = self.make_client(
                RunClient, owner=None, project=None, log_context=True
            )

            with self.assertRaises(PolyaxonClientException) as report_error:
                _get_client_context(client, include_run=True)
            with self.assertRaises(PolyaxonClientException) as uuid_error:
                _ = client.run_uuid

        message = str(report_error.exception)
        assert message == str(uuid_error.exception)
        assert f"local cache · {run_path}" in message
        assert f"owner: global cache · {project_path}" in message
        assert f"project: global cache · {project_path}" in message
        assert logs.output == [
            f"INFO:polyaxon.cli:Using cached project `{OWNER}/{PROJECT}` "
            f"from `{project_path}`."
        ]

    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_cached_run_without_uuid_is_ignored(self, log_info, log_warning):
        RunConfigManager.set_config(
            V1Run(owner=OWNER, project=PROJECT), visibility="local"
        )
        client, _ = self.make_client(RunClient, log_context=True)

        assert client.run_uuid is None
        log_info.assert_not_called()
        log_warning.assert_not_called()

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_initializer_client_defaults_to_quiet(
        self, log_info, log_warning, stdout, stderr
    ):
        from polyaxon._client.init import get_client_or_raise

        self.cache_project()
        self.cache_run(project=PROJECT)
        client = get_client_or_raise()

        assert client.log_context is False
        assert client.run_uuid == CACHED_UUID
        log_info.assert_not_called()
        log_warning.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    def test_owner_setter_marks_same_value_explicit(self):
        project_path = self.cache_project()
        run_path = self.cache_run(project=PROJECT)
        client, _ = self.make_client(RunClient, owner=None, project=None)

        client.set_owner(OWNER)

        fields, _ = _get_client_context(client, include_run=True)
        assert fields[0][1] == OWNER
        assert fields[0][2].kind == "explicit"
        assert fields[0][2].path is None
        assert fields[1][2].kind == "local cache"
        assert fields[1][2].path == project_path
        assert fields[-1][2].path == run_path
        assert client.run_uuid == CACHED_UUID

    def test_project_setter_marks_same_value_explicit(self):
        project_path = self.cache_project()
        run_path = self.cache_run(project=PROJECT)
        client, _ = self.make_client(RunClient, owner=None, project=None)

        client.set_project(PROJECT)

        fields, _ = _get_client_context(client, include_run=True)
        assert fields[1][1] == PROJECT
        assert fields[1][2].kind == "explicit"
        assert fields[1][2].path is None
        assert fields[0][2].kind == "local cache"
        assert fields[0][2].path == project_path
        assert fields[-1][2].path == run_path
        assert client.run_uuid == CACHED_UUID

    def test_owner_setter_keeps_explicit_provenance_after_round_trip(self):
        project_path = self.cache_project()
        run_path = self.cache_run(project=PROJECT)
        client, _ = self.make_client(RunClient, owner=None, project=None)

        client.set_owner("other-owner")
        with self.assertRaises(PolyaxonClientException) as error:
            _ = client.run_uuid
        assert "owner: explicit" in str(error.exception)

        client.set_owner(OWNER)

        fields, _ = _get_client_context(client, include_run=True)
        assert fields[0][1] == OWNER
        assert fields[0][2].kind == "explicit"
        assert fields[0][2].path is None
        assert fields[1][2].kind == "local cache"
        assert fields[1][2].path == project_path
        assert fields[-1][2].path == run_path
        assert client.run_uuid == CACHED_UUID

    def test_project_setter_keeps_explicit_provenance_after_round_trip(self):
        project_path = self.cache_project()
        run_path = self.cache_run(project=PROJECT)
        client, _ = self.make_client(RunClient, owner=None, project=None)

        client.set_project(CACHED_PROJECT)
        with self.assertRaises(PolyaxonClientException) as error:
            _ = client.run_uuid
        assert "project: explicit" in str(error.exception)

        client.set_project(PROJECT)

        fields, _ = _get_client_context(client, include_run=True)
        assert fields[1][1] == PROJECT
        assert fields[1][2].kind == "explicit"
        assert fields[1][2].path is None
        assert fields[0][2].kind == "local cache"
        assert fields[0][2].path == project_path
        assert fields[-1][2].path == run_path
        assert client.run_uuid == CACHED_UUID

    def test_owner_setter_updates_team_and_provenance(self):
        self.cache_project(owner=f"{OWNER}/old-team")
        client, _ = self.make_client(
            RunClient, owner=None, project=None, run_uuid=NEW_UUID
        )

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

    def test_loading_offline_run_replaces_cached_identity(self):
        self.cache_run()
        self.cache_project(project=CACHED_PROJECT)
        client, _ = self.make_client(RunClient, owner=None, project=None)
        persisted = V1Run(uuid=NEW_UUID, owner="other-owner", project=PROJECT)
        (self.directory / ctx_paths.CONTEXT_LOCAL_RUN).write_text(persisted.to_json())

        restored = RunClient.load_offline_run(
            path=str(self.directory), run_client=client, reset_project=False
        )

        assert restored is client
        assert client.run_uuid == NEW_UUID
        fields, _ = _get_client_context(client, include_run=True)
        assert fields[-1][1] == NEW_UUID
        assert fields[-1][2].kind == "explicit"
        assert fields[-1][2].path is None
        assert (client.owner, client.project) == ("other-owner", PROJECT)
        assert fields[0][1] == "other-owner"
        assert fields[1][1] == PROJECT
        assert all(source.kind == "explicit" for _, _, source in fields)
        assert all(source.path is None for _, _, source in fields)

    def test_loading_offline_run_keeps_target_when_resetting_project(self):
        self.cache_run()
        self.cache_project(project=CACHED_PROJECT)
        client, _ = self.make_client(RunClient, owner=None, project=None)
        original_fields, _ = _get_client_context(client)
        persisted = V1Run(uuid=NEW_UUID, owner="other-owner", project=PROJECT)
        (self.directory / ctx_paths.CONTEXT_LOCAL_RUN).write_text(persisted.to_json())

        restored = RunClient.load_offline_run(
            path=str(self.directory), run_client=client, reset_project=True
        )

        assert restored is client
        assert client.run_uuid == NEW_UUID
        fields, _ = _get_client_context(client, include_run=True)
        assert fields[-1][1] == NEW_UUID
        assert fields[-1][2].kind == "explicit"
        assert fields[-1][2].path is None
        assert (client.owner, client.project) == (OWNER, CACHED_PROJECT)
        assert fields[:2] == original_fields

    @patch("traceml.tracking.run.Run._set_exit_handler")
    def test_tracking_new_run_replaces_cached_conflict(self, set_exit_handler):
        from traceml.tracking.run import Run

        self.cache_run()
        sdk = SimpleNamespace(is_async=False, config=None, runs_v1=MagicMock())
        sdk.runs_v1.create_run.return_value = V1Run(
            uuid=NEW_UUID, owner=OWNER, project=PROJECT
        )

        client = Run(
            owner=OWNER,
            project=PROJECT,
            client=sdk,
            is_new=True,
            track_code=False,
            track_env=False,
            track_logs=False,
            artifacts_path=str(self.directory / "artifacts"),
            collect_artifacts=False,
            collect_resources=False,
        )

        assert client.run_uuid == NEW_UUID
        sdk.runs_v1.create_run.assert_called_once()

    @patch("traceml.tracking.run.Run._set_exit_handler")
    def test_tracking_existing_run_preserves_cached_conflict(self, set_exit_handler):
        from traceml.tracking.run import Run

        self.cache_run()
        sdk = SimpleNamespace(is_async=False, config=None, runs_v1=MagicMock())
        sdk.runs_v1.create_run.return_value = V1Run(
            uuid=NEW_UUID, owner=OWNER, project=PROJECT
        )

        client = Run(
            owner=OWNER,
            project=PROJECT,
            client=sdk,
            is_new=False,
            track_code=False,
            track_env=False,
            track_logs=False,
            artifacts_path=str(self.directory / "artifacts"),
            collect_artifacts=False,
            collect_resources=False,
        )

        assert client.run_data.uuid == CACHED_UUID
        with self.assertRaises(PolyaxonClientException):
            client.get_namespace()

        sdk.runs_v1.create_run.assert_not_called()
        sdk.runs_v1.get_run_namespace.assert_not_called()
