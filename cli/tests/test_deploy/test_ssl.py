from polyaxon._deploy.schemas.ssl import SSLConfig
from polyaxon._utils.test_utils import BaseTestCase


class TestSSLConfig(BaseTestCase):
    def test_ssl_config(self):
        config_dict = {"enabled": True, "secretName": "foo", "path": "/etc/ssl"}
        config = SSLConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict
