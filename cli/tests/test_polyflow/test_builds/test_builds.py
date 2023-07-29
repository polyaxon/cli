import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon.polyflow import V1Build
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.builds_mark
class TestBuildsConfigs(BaseTestCase):
    def test_builds_config(self):
        config_dict = {}

        with self.assertRaises(ValidationError):
            V1Build.from_dict(config_dict)

        config_dict["connections"] = "test"
        with self.assertRaises(ValidationError):
            V1Build.from_dict(config_dict)
        config_dict.pop("connections")

        # Add connection
        config_dict["connection"] = "test"
        with self.assertRaises(ValidationError):
            V1Build.from_dict(config_dict)

        # Add component ref
        config_dict["hubRef"] = "comp1"
        config = V1Build.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add params
        config_dict["params"] = "comp1"
        with self.assertRaises(ValidationError):
            V1Build.from_dict(config_dict)

        config_dict["params"] = {"param1": {"value": "value1"}}
        config = V1Build.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add runPatch
        config_dict["runPatch"] = {"environment": {}}
        config = V1Build.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add presets
        config_dict["presets"] = ["p1", "p2"]
        config = V1Build.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
