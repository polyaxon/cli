from clipped.compact.pydantic import ValidationError
from polyaxon._deploy.schemas.throttle import ThrottleConfig
from polyaxon._utils.test_utils import BaseTestCase


class TestThrottleConfig(BaseTestCase):
    def test_throttle_config(self):
        config_dict = {"rates": {"run": 600, "run_status": 90}}
        config = ThrottleConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict

        config = ThrottleConfig.from_dict({})
        assert config.to_dict() == {}
        assert config.to_light_dict() == {}

    def test_throttle_config_wrong_rate(self):
        with self.assertRaises(ValidationError):
            ThrottleConfig.from_dict({"rates": {"run": "fast"}})
