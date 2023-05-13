import pytest

from polyaxon.schemas.api.user import UserConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.api_mark
class TestUserConfigs(BaseTestCase):
    def test_user_config(self):
        config_dict = {
            "username": "username",
            "email": "user@domain.com",
            "name": "foo bat",
            "theme": 1,
        }
        config = UserConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict
