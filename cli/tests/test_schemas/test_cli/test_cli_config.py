import pytest

from polyaxon.schemas.cli.cli_config import CliConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.schemas_mark
class TestCliConfig(BaseTestCase):
    def test_cli_config(self):
        config_dict = {
            "current_version": "0.0.1",
            "installation": {"key": "uuid", "version": "1.1.4-rc11", "dist": "foo"},
            "compatibility": {"cli": {"min": "0.0.4", "latest": "1.1.4"}},
            "log_handler": None,
        }
        config = CliConfig.from_dict(config_dict)
        config_to_dict = config.to_dict()
        config_to_dict.pop("last_check")
        assert config._INTERVAL == 30 * 60
        assert config_to_dict != config_dict
        config_dict.pop("log_handler")
        assert config_to_dict == config_dict
