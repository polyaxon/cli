from mock import patch
import pytest

from polyaxon._cli.check import check
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliCheck(BaseCommandTestCase):
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
