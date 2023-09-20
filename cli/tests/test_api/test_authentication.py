import pytest

from clipped.compact.pydantic import ValidationError

from polyaxon._env_vars.keys import ENV_KEYS_AUTH_TOKEN, ENV_KEYS_AUTH_USERNAME
from polyaxon._schemas.authentication import AccessTokenConfig, V1Credentials
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.api_mark
class TestAccessConfigs(BaseTestCase):
    def test_access_token_wrong_config(self):
        config_dict = {
            ENV_KEYS_AUTH_USERNAME: "username",
            ENV_KEYS_AUTH_TOKEN: "sdfsdf098sdf80s9dSDF800",
            "foo": "bar",
        }
        config = AccessTokenConfig.from_dict(config_dict)
        assert config.to_dict() != config_dict
        config_dict.pop("foo")
        assert config.to_dict() == config_dict

    def test_access_token_config(self):
        config_dict = {
            ENV_KEYS_AUTH_USERNAME: "username",
            ENV_KEYS_AUTH_TOKEN: "sdfsdf098sdf80s9dSDF800",
        }
        config = AccessTokenConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict

    def test_credentials_wrong_config(self):
        config_dict = {"username": "username", "password": "super-secret", "foo": "bar"}
        with self.assertRaises(ValidationError):
            V1Credentials.from_dict(config_dict)

    def test_credentials_config(self):
        config_dict = {"username": "username", "password": "super-secret"}
        config = V1Credentials.from_dict(config_dict)
        assert config.to_dict() == config_dict
