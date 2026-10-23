from mock import MagicMock, patch
import os
import pytest
import subprocess
import sys
import tempfile
from textwrap import dedent

from polyaxon import settings
from polyaxon._contexts import paths as ctx_paths
from polyaxon.cli import cli
from tests.test_cli.utils import BaseCommandTestCase


HEAVY_STARTUP_MODULES = {
    "kubernetes",
    "polyaxon._client.client",
    "polyaxon._cli.session",
    "polyaxon._flow",
    "polyaxon._polyaxonfile",
    "polyaxon._sdk.api",
    "polyaxon.settings",
    "rich",
}


@pytest.mark.cli_mark
class TestCliStartup(BaseCommandTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch.object(
            ctx_paths,
            "CONTEXT_USER_POLYAXON_PATH",
            os.path.join(directory.name, ".polyaxon"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    def assert_no_command_dependencies(self, show_help):
        code = dedent(
            """
            from contextlib import redirect_stdout
            from io import StringIO
            import sys

            from polyaxon.cli import cli

            if {show_help!r}:
                with redirect_stdout(StringIO()):
                    cli.main(["--help"], standalone_mode=False)

            heavy_modules = {heavy_modules!r}
            print("\\n".join(sorted(heavy_modules.intersection(sys.modules))))
            """
        ).format(heavy_modules=HEAVY_STARTUP_MODULES, show_help=show_help)

        result = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
        )

        assert result.stdout.strip() == ""

    def test_cli_import_does_not_load_command_dependencies(self):
        self.assert_no_command_dependencies(show_help=False)

    def test_cli_help_does_not_load_command_dependencies(self):
        self.assert_no_command_dependencies(show_help=True)

    def test_cli_help_lists_commands(self):
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        for command in ["artifacts", "components", "models", "ops", "project", "run"]:
            assert command in result.output
        rows = [line.strip() for line in result.output.splitlines()]
        for command, alias in [("project", "projects"), ("sandbox", "sbx")]:
            command_rows = [row for row in rows if row.startswith(command)]
            assert len(command_rows) == 1
            assert command_rows[0].startswith("{} (aliases: {})".format(command, alias))
            assert not [row for row in rows if row.startswith(alias)]

    def test_sandbox_commands_skip_version_check(self):
        cli_config = MagicMock(installation=None)
        cli_config.__bool__.return_value = False
        cases = [("project", True), ("sandbox", False), ("sbx", False)]
        for command, checks_version in cases:
            with (
                self.subTest(command=command),
                patch.object(settings, "set_cli_config"),
                patch.object(settings, "CLI_CONFIG", cli_config),
                patch("polyaxon._cli.session.set_versions_config") as set_versions,
                patch("polyaxon.cli.check_cli_version") as check_version,
            ):
                result = self.runner.invoke(cli, [command, "--help"])

                assert result.exit_code == 0
                assert set_versions.called is checks_version
                assert check_version.called is checks_version
