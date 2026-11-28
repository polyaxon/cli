from contextlib import contextmanager
from mock import patch
import os
import tempfile

from click.testing import CliRunner

from polyaxon._utils.test_utils import BaseTestCase


@contextmanager
def temp_cwd():
    """Run in an empty temporary working directory, like Click's deprecated
    `CliRunner.isolated_filesystem`."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as directory:
        os.chdir(directory)
        try:
            yield directory
        finally:
            os.chdir(cwd)


class BaseCommandTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.runner = CliRunner()
        self.mock_config()

    def mock_config(self):
        patcher = patch("polyaxon._managers.client.ClientConfigManager.get_value")
        patcher.start()
        self.addCleanup(patcher.stop)
