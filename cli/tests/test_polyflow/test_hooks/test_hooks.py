import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow import V1Hook
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.hooks_mark
class TestHooksConfigs(BaseTestCase):
    def test_hooks_config(self):
        config_dict = {}

        with self.assertRaises(ValidationError):
            V1Hook.from_dict(config_dict)

        config_dict["connections"] = "test"
        with self.assertRaises(ValidationError):
            V1Hook.from_dict(config_dict)
        config_dict.pop("connections")

        # Add connection
        config_dict["connection"] = "test"
        with self.assertRaises(ValidationError):
            V1Hook.from_dict(config_dict)

        # Add component ref
        config_dict["hubRef"] = "comp1"
        config = V1Hook.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add a trigger policy
        config_dict["trigger"] = "not-supported"
        with self.assertRaises(ValidationError):
            V1Hook.from_dict(config_dict)

        # Add trigger
        config_dict["trigger"] = "succeeded"
        config = V1Hook.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add params
        config_dict["params"] = "comp1"
        with self.assertRaises(ValidationError):
            V1Hook.from_dict(config_dict)

        config_dict["params"] = {"param1": {"value": "value1"}}
        config = V1Hook.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add presets
        config_dict["presets"] = ["p1", "p2"]
        config = V1Hook.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add conditions
        config_dict["conditions"] = "outputs.loss > 0.1"
        config = V1Hook.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
