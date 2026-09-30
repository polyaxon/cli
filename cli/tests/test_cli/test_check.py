from mock import patch
from pathlib import Path
import pytest
import tempfile

from polyaxon._cli.check import check
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliCheck(BaseCommandTestCase):
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_check_shared_file_validates_params_without_submission(self, create_run):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "job.yml"
            source.write_text(
                "strictParams: true\n"
                "inputs: [{name: count, type: int}]\n"
                "run:\n"
                "  kind: job\n"
                "  container:\n"
                "    image: busybox:1.36\n"
                "    command: [sh, '-c']\n"
                "    args: ['echo {{ count }}']\n"
            )
            for params, exit_code in (
                (["-P", "count=3"], 0),
                (["-P", "count=invalid"], 1),
                (["-P", "count=3", "-P", "extra=1"], 1),
            ):
                with self.subTest(params=params):
                    result = self.runner.invoke(check, ["-f", str(source), *params])

                    assert result.exit_code == exit_code, (
                        result.output,
                        result.exception,
                    )
                    if "extra=1" in params:
                        assert "undeclared param" in result.output
                    create_run.assert_not_called()

    def test_check_strict_params(self):
        for options, exit_code in (
            ([], 0),
            (["--strict-params"], 1),
            (["--no-strict-params"], 0),
        ):
            with self.subTest(options=options):
                result = self.runner.invoke(
                    check,
                    [
                        "--file=tests/fixtures/plain/simple_job.yml",
                        "-P",
                        "extra=1",
                        *options,
                    ],
                )
                assert result.exit_code == exit_code, (result.output, result.exception)
                if exit_code:
                    assert "undeclared param" in result.output

    @patch("polyaxon._polyaxonfile.check.check_polyaxonfile")
    def test_check_file(self, check_polyaxonfile):
        self.runner.invoke(check)
        assert check_polyaxonfile.call_count == 1

    @patch("polyaxon._polyaxonfile.check.check_polyaxonfile")
    @patch("polyaxon._cli.check.Printer.decorate_format_value")
    def test_check_file_version(self, decorate_format_value, check_polyaxonfile):
        self.runner.invoke(check, ["--version"])
        assert check_polyaxonfile.call_count == 1
        assert decorate_format_value.call_count == 1
