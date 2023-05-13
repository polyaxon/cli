import pytest

from polyaxon.env_vars.keys import EV_KEYS_HOME
from polyaxon.schemas.api.home import HomeConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.api_mark
class TestHomeConfig(BaseTestCase):
    def test_home_wrong_config(self):
        config_dict = {EV_KEYS_HOME: "foo/bar/moo", "foo": "bar"}
        config = HomeConfig.from_dict(config_dict)
        assert config.to_dict() != config_dict
        config_dict.pop("foo")
        assert config.to_dict() == config_dict

    def test_home_config(self):
        config_dict = {EV_KEYS_HOME: "foo/bar/moo"}
        config = HomeConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict
