import pytest

from mock import patch

from polyaxon._cli.config import config
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliConfig(BaseCommandTestCase):
    @patch("polyaxon._managers.client.ClientConfigManager.is_initialized")
    def test_config_list_checks_initialized(self, is_initialized):
        is_initialized.return_value = False
        self.runner.invoke(config, ["show"])
        assert is_initialized.call_count == 1

    @patch("polyaxon._managers.client.ClientConfigManager.is_initialized")
    @patch("polyaxon._managers.client.ClientConfigManager.CONFIG")
    def test_config_list_gets_default_config(self, default_config, is_initialized):
        is_initialized.return_value = False
        self.runner.invoke(config, ["show"])
        assert default_config.call_count == 1

    @patch("polyaxon._managers.client.ClientConfigManager.is_initialized")
    @patch("polyaxon._managers.client.ClientConfigManager.get_config")
    def test_config_list_gets_file_config(self, get_config, is_initialized):
        is_initialized.return_value = True
        self.runner.invoke(config, ["show"])
        assert get_config.call_count == 1
