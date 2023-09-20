import pytest

from mock import patch

from polyaxon._cli.check import check
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliCheck(BaseCommandTestCase):
    @patch("polyaxon._cli.check.check_polyaxonfile")
    def test_check_file(self, check_polyaxonfile):
        self.runner.invoke(check)
        assert check_polyaxonfile.call_count == 1

    @patch("polyaxon._cli.check.check_polyaxonfile")
    @patch("polyaxon._cli.check.Printer.decorate_format_value")
    def test_check_file_version(self, decorate_format_value, check_polyaxonfile):
        self.runner.invoke(check, ["--version"])
        assert check_polyaxonfile.call_count == 1
        assert decorate_format_value.call_count == 1
