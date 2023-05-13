from pydantic import ValidationError

from polyaxon.deploy.schemas.root_user import RootUserConfig
from polyaxon.utils.test_utils import BaseTestCase


class TestRootUserConfig(BaseTestCase):
    def test_root_user_config(self):
        bad_config_dicts = [
            {"username": False, "password": "foo", "email": "sdf"},
            {"username": "sdf", "password": "foo", "email": "sdf"},
            {"username": "sdf", "password": "foo", "email": "sdf@boo"},
            {"username": "foo.bar", "password": "foo", "email": "foo@bar.com"},
            {"username": "foo bar", "password": "foo", "email": "foo@bar.com"},
        ]

        for config_dict in bad_config_dicts:
            with self.assertRaises(ValidationError):
                RootUserConfig.from_dict(config_dict)

        config_dict = {"username": "sdf", "password": "foo"}

        config = RootUserConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {"username": "sdf", "password": "foo", "email": "foo@bar.com"}

        config = RootUserConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict
