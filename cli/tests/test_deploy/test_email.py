from clipped.compact.pydantic import ValidationError

from polyaxon.deploy.schemas.email import EmailConfig
from polyaxon.utils.test_utils import BaseTestCase


class TestEmailConfig(BaseTestCase):
    def test_email_config(self):
        config_dict = {
            "host": "dsf",
            "port": "sdf",
            "useTls": 123,
            "hostUser": "sdf",
            "hostPassword": "sdf",
        }
        with self.assertRaises(ValidationError):
            EmailConfig.from_dict(config_dict)

        config_dict = {
            "emailFrom" "host": "dsf",
            "port": "sdf",
            "useTls": True,
            "hostUser": "sdf",
            "hostPassword": "sdf",
        }
        with self.assertRaises(ValidationError):
            EmailConfig.from_dict(config_dict)

        config_dict = {
            "host": "dsf",
            "port": 123,
            "useTls": False,
            "hostUser": "sdf",
            "hostPassword": "sdf",
        }
        config = EmailConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "from": "foo@bar.com",
            "host": "mail.bar.com",
            "port": 25,
            "useTls": True,
            "hostUser": "sdf",
            "hostPassword": "sdf",
        }
        config = EmailConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict
