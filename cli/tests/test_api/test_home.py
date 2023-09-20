import pytest

from polyaxon._env_vars.keys import ENV_KEYS_HOME
from polyaxon._schemas.home import HomeConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.api_mark
class TestHomeConfig(BaseTestCase):
    def test_home_wrong_config(self):
        config_dict = {ENV_KEYS_HOME: "foo/bar/moo", "foo": "bar"}
        config = HomeConfig.from_dict(config_dict)
        assert config.to_dict() != config_dict
        config_dict.pop("foo")
        assert config.to_dict() == config_dict

    def test_home_config(self):
        config_dict = {ENV_KEYS_HOME: "foo/bar/moo"}
        config = HomeConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict
