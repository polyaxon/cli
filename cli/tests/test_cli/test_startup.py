import pytest
import subprocess
import sys

from click.testing import CliRunner

from polyaxon.cli import cli


HEAVY_STARTUP_MODULES = {
    "kubernetes",
    "polyaxon._client.client",
    "polyaxon._cli.session",
    "polyaxon._flow",
    "polyaxon._polyaxonfile",
    "polyaxon._sdk.api",
    "polyaxon.settings",
}


@pytest.mark.cli_mark
def test_cli_import_does_not_load_command_dependencies():
    code = """
import sys

from polyaxon.cli import cli

heavy_modules = {heavy_modules!r}
print("\\n".join(sorted(heavy_modules.intersection(sys.modules))))
""".format(heavy_modules=HEAVY_STARTUP_MODULES)

    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""


@pytest.mark.cli_mark
def test_cli_help_lists_commands():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in ["artifacts", "components", "models", "ops", "project", "run"]:
        assert command in result.output
