from clipped.compact.pydantic import ValidationError

from polyaxon.deploy.schemas.security_context import SecurityContextConfig
from polyaxon.utils.test_utils import BaseTestCase


class TestSecurityContentConfig(BaseTestCase):
    def test_security_content_config(self):
        config_dict = {}
        config = SecurityContextConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {"enabled": True}
        SecurityContextConfig.from_dict(config_dict)

        config_dict = {"enabled": False}
        SecurityContextConfig.from_dict(config_dict)

        with self.assertRaises(ValidationError):
            config_dict = {"user": "foo"}
            SecurityContextConfig.from_dict(config_dict)

        with self.assertRaises(ValidationError):
            config_dict = {"user": 120}
            SecurityContextConfig.from_dict(config_dict)

        with self.assertRaises(ValidationError):
            config_dict = {"runAsGroup": "foo"}
            SecurityContextConfig.from_dict(config_dict)

        with self.assertRaises(ValidationError):
            config_dict = {"runAsGroup": 120}
            SecurityContextConfig.from_dict(config_dict)

        with self.assertRaises(ValidationError):
            config_dict = {"runAsUser": "sdf", "runAsGroup": 120}
            SecurityContextConfig.from_dict(config_dict)

        with self.assertRaises(ValidationError):
            config_dict = {"user": 120, "group": 120}
            SecurityContextConfig.from_dict(config_dict)

        config_dict = {"runAsUser": 120, "runAsGroup": 120}
        config = SecurityContextConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {"enabled": True, "runAsUser": 120, "runAsGroup": 120}
        config = SecurityContextConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict
