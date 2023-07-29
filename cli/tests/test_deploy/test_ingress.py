from clipped.compact.pydantic import ValidationError

from polyaxon.deploy.schemas.ingress import IngressConfig
from polyaxon.utils.test_utils import BaseTestCase


class TestIngressConfig(BaseTestCase):
    def test_ingress_config(self):
        config_dict = {"enabled": "sdf"}

        with self.assertRaises(ValidationError):
            IngressConfig.from_dict(config_dict)

        config_dict = {"enabled": False}

        config = IngressConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "enabled": False,
            "path": "/*",
            "tls": [{"hosts": "bar.com"}],
            "annotations": {"a": "b"},
        }

        config = IngressConfig.from_dict(config_dict)

        assert config.to_light_dict() == config_dict
