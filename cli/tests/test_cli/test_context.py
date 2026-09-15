from io import StringIO
import os
import pytest
import re
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import click
from rich.console import Console
from rich.theme import Theme

from clipped.formatting import Printer
from polyaxon._cli.context import _print_context, report_client_context, resolve_project
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.getters import get_local_owner
from polyaxon._env_vars.getters._context import _ContextSource
from polyaxon._env_vars.getters.project import _get_project_context, _ProjectContext
from polyaxon._env_vars.getters.run import _get_project_run_context
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_user import V1User
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliContext(BaseCommandTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        local_cache = os.path.join(directory.name, "local", ".polyaxon")
        global_cache = os.path.join(directory.name, "global", ".polyaxon")
        patcher = patch.object(ctx_paths, "CONTEXT_USER_POLYAXON_PATH", global_cache)
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
        self.make_console()

    def make_console(self, width=160, color=False):
        theme = Theme(
            {
                name: Printer.stderr_console.get_style(name)
                for name in ("header", "warning")
            }
        )
        patcher = patch.object(
            Printer,
            "stderr_console",
            Console(
                stderr=True,
                width=width,
                force_terminal=color,
                color_system="standard" if color else None,
                no_color=not color,
                theme=theme,
            ),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_context_keeps_sources_on_their_rows(self, stdout, stderr):
        _print_context(
            [
                (
                    "Owner",
                    "acme",
                    _ContextSource("global cache", "/home/user/.polyaxon/.user"),
                ),
                ("Project", "quick-start", _ContextSource()),
            ]
        )

        output = stderr.getvalue()
        assert stdout.getvalue() == ""
        assert output.splitlines()[0] == "Context:"
        assert [
            line.rstrip().split(None, 2)
            for line in output.splitlines()[1:]
            if line.strip()
        ] == [
            ["Owner", "acme", "global cache · /home/user/.polyaxon/.user"],
            ["Project", "quick-start", "explicit"],
        ]
        assert "\x1b[" not in output

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_project_team_is_consistent_in_cli_and_python_reporting(
        self, stdout, stderr
    ):
        source = _ContextSource("local cache", "/work/.polyaxon/.project")
        context = _ProjectContext("acme", "team", "quick-start", source, source)

        with self.assertLogs("polyaxon.cli", level="INFO") as logs:
            context.report()
        _print_context(context.fields())

        assert logs.output == [
            "INFO:polyaxon.cli:Using cached project `acme/team/quick-start` "
            f"from `{source.path}`."
        ]
        output = " ".join(stderr.getvalue().split())
        assert stdout.getvalue() == ""
        assert "Owner acme/team" in output
        assert "Project quick-start" in output

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_context_uses_cli_heading_and_neutral_value_styles(self, stdout, stderr):
        self.make_console(color=True)
        _print_context(
            [("Project", "project-a", _ContextSource("local cache", "/work/.project"))]
        )

        output = stderr.getvalue()
        assert stdout.getvalue() == ""
        assert "\x1b[33mContext:\x1b[0m" in output
        assert "\x1b[1mproject-a" in output
        assert "\x1b[2mlocal cache · /work/.project" in output

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_context_wraps_without_losing_literal_values(self, stdout, stderr):
        run_uuid = "11111111111111111111111111111111"
        path = "/work/a directory[red]/:rocket:/another-long-directory/.polyaxon/.run"
        for width in (60, 80, 160):
            with self.subTest(width=width):
                self.make_console(width=width)
                stderr.seek(0)
                stderr.truncate(0)
                _print_context(
                    [
                        ("Owner", "owner", _ContextSource()),
                        ("Project", "[bold]project", _ContextSource()),
                        ("Run", run_uuid, _ContextSource("local cache", path)),
                    ]
                )

                output = stderr.getvalue()
                assert stdout.getvalue() == ""
                compact = "".join(output.split())
                assert run_uuid in compact
                assert "[bold]project" in compact
                assert "".join(path.split()) in compact
                assert all(len(line) <= width for line in output.splitlines())

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_context_keeps_incomplete_ownership_warning_separate(self, stdout, stderr):
        self.make_console(color=True)
        _print_context(
            [("Run", "run-uuid", _ContextSource("local cache", "/work/.run"))],
            incomplete_run=True,
        )

        output = stderr.getvalue()
        assert stdout.getvalue() == ""
        assert output.count("Context:") == 1
        assert "\x1b[33mContext:" in output
        assert "\x1b[35m" in output
        plain = re.sub(r"\x1b\[[0-9;]*m", "", output)
        assert "Cached owner/project metadata is incomplete;" in plain

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon._cli.context._get_client_context")
    def test_client_reporting_uses_context_adapter(self, get_context, stdout, stderr):
        source = _ContextSource("local cache", "/work/.polyaxon/.run")
        get_context.return_value = ([("Run", "run-uuid", source)], True)
        client = SimpleNamespace()

        report_client_context(client, include_run=True, show_context=True)

        get_context.assert_called_once_with(client, include_run=True)
        output = stderr.getvalue()
        assert stdout.getvalue() == ""
        assert output.count("Context:") == 1
        assert source.path in output
        assert "Cached owner/project metadata is incomplete;" in output

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon._cli.context._get_client_context")
    def test_client_reporting_can_be_disabled(self, get_context, stdout, stderr):
        source = _ContextSource("local cache", "/work/.polyaxon/.run")
        get_context.return_value = ([("Run", "run-uuid", source)], True)
        client = SimpleNamespace()

        report_client_context(client, include_run=True, show_context=False)

        get_context.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon._cli.context._get_client_context")
    def test_no_op_client_reporting_stays_quiet(self, get_context, stdout, stderr):
        get_context.return_value = None
        client = SimpleNamespace()

        report_client_context(client, include_run=True, show_context=True)

        get_context.assert_called_once_with(client, include_run=True)
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon._cli.context._get_client_context")
    def test_no_op_client_reporting_can_be_disabled(self, get_context, stdout, stderr):
        get_context.return_value = None
        client = SimpleNamespace()

        report_client_context(client, include_run=True, show_context=False)

        get_context.assert_not_called()
        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    def test_explicit_context_stays_quiet(self, stdout, stderr):
        _print_context(
            [
                ("Owner", "owner", _ContextSource()),
                ("Project", "project-a", _ContextSource()),
                ("Run", "run-uuid", _ContextSource()),
            ]
        )

        assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon._cli.context._get_project_context")
    def test_reporting_can_be_disabled_regardless_of_ambient_context(
        self, get_context, stdout, stderr
    ):
        source = _ContextSource("local cache", "/work/.polyaxon/.project")
        get_context.return_value = _ProjectContext(
            "owner", None, "project", source, source
        )
        for ambient_show_context in (False, True):
            with self.subTest(ambient_show_context=ambient_show_context):
                with click.Context(
                    click.Command("test"), obj={"show_context": ambient_show_context}
                ):
                    assert resolve_project(show_context=False) == (
                        "owner",
                        None,
                        "project",
                    )

                assert stdout.getvalue() == stderr.getvalue() == ""

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon._cli.context._get_project_context")
    def test_reporting_can_be_enabled_regardless_of_ambient_context(
        self, get_context, stdout, stderr
    ):
        source = _ContextSource("local cache", "/work/.polyaxon/.project")
        get_context.return_value = _ProjectContext(
            "owner", None, "project", source, source
        )
        for ambient_show_context in (False, True):
            with self.subTest(ambient_show_context=ambient_show_context):
                stderr.seek(0)
                stderr.truncate(0)
                with click.Context(
                    click.Command("test"), obj={"show_context": ambient_show_context}
                ):
                    assert resolve_project(show_context=True) == (
                        "owner",
                        None,
                        "project",
                    )

                output = stderr.getvalue()
                assert stdout.getvalue() == ""
                assert output.count("Context:") == 1
                assert source.path in output

    @patch("sys.stderr", new_callable=StringIO)
    @patch("sys.stdout", new_callable=StringIO)
    @patch("polyaxon.logger.logger.warning")
    @patch("polyaxon.logger.logger.info")
    def test_getters_resolve_without_reporting(
        self, log_info, log_warning, stdout, stderr
    ):
        UserConfigManager.set_config(V1User(organization="owner"))
        ProjectConfigManager.set_config(
            V1Project(owner="owner", name="project"), visibility="local"
        )
        run_uuid = "11111111111111111111111111111111"
        RunConfigManager.set_config(
            V1Run(uuid=run_uuid, owner="owner", project="project"), visibility="local"
        )

        for is_cli in (False, True):
            with self.subTest(is_cli=is_cli):
                with click.Context(click.Command("test"), obj={"show_context": True}):
                    assert get_local_owner(is_cli=is_cli) == "owner"
                    project_context = _get_project_context(is_cli=is_cli)
                    assert (
                        project_context.owner,
                        project_context.team,
                        project_context.project,
                    ) == ("owner", None, "project")

                    project_context, run_context = _get_project_run_context(
                        is_cli=is_cli
                    )
                    assert (
                        project_context.owner,
                        project_context.team,
                        project_context.project,
                        run_context.uuid,
                    ) == ("owner", None, "project", run_uuid)

                assert stdout.getvalue() == stderr.getvalue() == ""
                log_info.assert_not_called()
                log_warning.assert_not_called()
