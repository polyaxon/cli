from mock import patch

from click.testing import CliRunner

from polyaxon.utils.test_utils import BaseTestCase


class BaseCommandTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.runner = CliRunner()
        self.mock_config()

    def mock_config(self):
        patcher = patch("polyaxon.managers.client.ClientConfigManager.get_value")
        patcher.start()
        self.addCleanup(patcher.stop)
