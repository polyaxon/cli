import pytest

from polyaxon.env_vars.keys import ENV_KEYS_DEBUG, ENV_KEYS_HOST, ENV_KEYS_VERIFY_SSL
from polyaxon.schemas.client import ClientConfig
from polyaxon.services.auth import AuthenticationTypes
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.schemas_mark
class TestClientConfig(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.host = "http://localhost:8000"
        self.config = ClientConfig(host=self.host, version="v1", token="token")

    def test_client_config(self):
        config_dict = {
            ENV_KEYS_DEBUG: True,
            ENV_KEYS_HOST: "http://localhost:8000",
            ENV_KEYS_VERIFY_SSL: True,
        }
        config = ClientConfig.from_dict(config_dict)
        assert config.debug is True
        assert config.host == "http://localhost:8000"
        assert config.base_url == "http://localhost:8000/api/v1"
        assert config.verify_ssl is True

    def test_base_urls(self):
        assert self.config.base_url == "{}/api/v1".format(self.host)

    def test_is_managed(self):
        config = ClientConfig(host=None, is_managed=True)
        assert config.is_managed is True
        assert config.version == "v1"
        assert config.host == "http://localhost:8000"

    def test_get_headers(self):
        config = ClientConfig(host=None, is_managed=True)
        assert config.get_full_headers() == {}
        assert config.get_full_headers({"foo": "bar"}) == {"foo": "bar"}

        config = ClientConfig(token="token", host="host")

        assert config.get_full_headers() == {
            "Authorization": "{} {}".format(AuthenticationTypes.TOKEN, "token")
        }
        assert config.get_full_headers({"foo": "bar"}) == {
            "foo": "bar",
            "Authorization": "{} {}".format(AuthenticationTypes.TOKEN, "token"),
        }

        config.authentication_type = AuthenticationTypes.INTERNAL_TOKEN
        assert config.get_full_headers() == {
            "Authorization": "{} {}".format(AuthenticationTypes.INTERNAL_TOKEN, "token")
        }
        assert config.get_full_headers({"foo": "bar"}) == {
            "foo": "bar",
            "Authorization": "{} {}".format(
                AuthenticationTypes.INTERNAL_TOKEN, "token"
            ),
        }
