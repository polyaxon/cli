from io import StringIO
import os
import pytest
import tempfile
from unittest.mock import patch

from polyaxon import settings
from polyaxon._client.organization import AsyncOrganizationClient, OrganizationClient
from polyaxon._client.project import AsyncProjectClient, ProjectClient
from polyaxon._constants.globals import DEFAULT
from polyaxon._contexts import paths as ctx_paths
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._schemas.cli import CliConfig
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_user import V1User
from polyaxon._utils.test_utils import BaseTestCase


CLIENT_TYPES = (
    ProjectClient,
    AsyncProjectClient,
    OrganizationClient,
    AsyncOrganizationClient,
)


@pytest.mark.client_mark
class TestCachedOwnerContext(BaseTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        local_cache = os.path.join(directory.name, "local", ".polyaxon")
        global_cache = os.path.join(directory.name, "global", ".polyaxon")
        patcher = patch.object(ctx_paths, "CONTEXT_USER_POLYAXON_PATH", global_cache)
        patcher.start()
        self.addCleanup(patcher.stop)
        for manager in (UserConfigManager, ProjectConfigManager):
            patcher = patch.multiple(
                manager,
                CONFIG_PATH=None,
                _PROJECT=local_cache,
                _PROJECT_PATH=global_cache,
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        super().setUp()
        settings.CLI_CONFIG = CliConfig()

    def cache_owner(self):
        UserConfigManager.set_config(V1User(organization="owner/team"))
        return os.path.abspath(UserConfigManager.get_config_filepath(create=False))

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    def test_cached_owner_logging_defaults_to_quiet(self, log_info, stdout, stderr):
        cache_path = self.cache_owner()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client = client_type()

                assert (client.owner, client.team) == ("owner", "team")
                assert client._owner_source.path == cache_path
                assert client._owner_source.kind == "global cache"
                assert client.log_context is False

        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    def test_cached_owner_logging_can_be_disabled(self, log_info, stdout, stderr):
        cache_path = self.cache_owner()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client = client_type(log_context=False)

                assert (client.owner, client.team) == ("owner", "team")
                assert client._owner_source.path == cache_path
                assert client._owner_source.kind == "global cache"
                assert client.log_context is False

        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_cached_owner_logging_can_be_enabled(self, stdout, stderr):
        cache_path = self.cache_owner()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client = client_type(log_context=True)

                assert (client.owner, client.team) == ("owner", "team")
                assert client._owner_source.path == cache_path
                assert client._owner_source.kind == "global cache"
                assert client.log_context is True
                assert logs.output == [
                    "INFO:polyaxon.cli:Using cached owner `owner/team` "
                    f"from `{cache_path}`."
                ]

        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_cached_owner_logging_can_be_enabled_offline(self, stdout, stderr):
        cache_path = self.cache_owner()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                with self.assertLogs("polyaxon.cli", level="INFO") as logs:
                    client = client_type(is_offline=True, log_context=True)

                assert (client.owner, client.team) == ("owner", "team")
                assert client._owner_source.path == cache_path
                assert client._owner_source.kind == "global cache"
                assert client.log_context is True
                assert logs.output == [
                    "INFO:polyaxon.cli:Using cached owner `owner/team` "
                    f"from `{cache_path}`."
                ]

        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    def test_explicit_owner_stays_quiet(self, log_info, stdout, stderr):
        self.cache_owner()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client = client_type(owner="explicit/other-team", log_context=True)

                assert (client.owner, client.team) == ("explicit", "other-team")
                assert client._owner_source.kind == "explicit"
                assert client._owner_source.path is None

        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    def test_default_owner_stays_quiet(self, log_info, stdout, stderr):
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client = client_type(log_context=True)

                assert client.owner == DEFAULT
                assert client._owner_source.kind == "default"
                assert client._owner_source.path is None

        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    @patch.object(UserConfigManager, "get_config")
    def test_no_op_does_not_resolve_owner(self, get_config, log_info, stdout, stderr):
        self.cache_owner()
        for client_type in CLIENT_TYPES:
            with self.subTest(client_type=client_type):
                client = client_type(no_op=True, log_context=True)

                assert client.log_context is True

        get_config.assert_not_called()
        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    def test_project_cache_does_not_supply_project(self):
        cache_path = self.cache_owner()
        ProjectConfigManager.set_config(
            V1Project(owner="other-owner", name="cached-project"), visibility="local"
        )
        for client_type in (ProjectClient, AsyncProjectClient):
            with self.subTest(client_type=client_type):
                client = client_type(log_context=True)

                assert (client.owner, client.team, client.project) == (
                    "owner",
                    "team",
                    None,
                )
                context = client._project_context_snapshot()
                assert context.owner_source.path == cache_path
                assert context.project_source.path is None

    def test_project_cache_does_not_override_explicit_project(self):
        cache_path = self.cache_owner()
        ProjectConfigManager.set_config(
            V1Project(owner="other-owner", name="cached-project"), visibility="local"
        )
        for client_type in (ProjectClient, AsyncProjectClient):
            with self.subTest(client_type=client_type):
                client = client_type(project="explicit-project", log_context=True)

                assert (client.owner, client.team, client.project) == (
                    "owner",
                    "team",
                    "explicit-project",
                )
                context = client._project_context_snapshot()
                assert context.owner_source.path == cache_path
                assert context.project_source.path is None

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.info")
    def test_fully_qualified_project_stays_quiet(self, log_info, stdout, stderr):
        self.cache_owner()
        for client_type in (ProjectClient, AsyncProjectClient):
            with self.subTest(client_type=client_type):
                client = client_type(
                    project="explicit/other-team/project", log_context=True
                )

                assert (client.owner, client.team, client.project) == (
                    "explicit",
                    "other-team",
                    "project",
                )
                assert client._owner_source.path is None

        log_info.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""
