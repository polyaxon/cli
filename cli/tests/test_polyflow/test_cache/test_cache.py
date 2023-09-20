import pytest

from clipped.compact.pydantic import ValidationError

from polyaxon._flow import V1Cache
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.components_mark
class TestCacheConfigs(BaseTestCase):
    def test_cache_config(self):
        expected_config_dict = {"disable": True}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": 1}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": "t"}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()

        expected_config_dict = {"disable": False}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": 0}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": "f"}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()

        expected_config_dict = {
            "io": ["in1", "in2"],
            "sections": ["init", "containers"],
        }
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()

        expected_config_dict = {"disable": True, "ttl": 12, "io": ["in1", "in2"]}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": 1, "ttl": 12.2, "io": ["in1", "in2"]}
        with self.assertRaises(ValidationError):
            V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": 1, "ttl": "12", "io": ["in1", "in2"]}
        with self.assertRaises(ValidationError):
            V1Cache.from_dict(config_dict)

        expected_config_dict = {"disable": False, "sections": ["containers"]}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": False, "sections": ("containers",)}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": 0, "sections": ["containers"]}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"disable": "foo"}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"ttl": "foo"}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"ttl": "12.3"}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"sections": ["foo"]}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"sections": ["container"]}  # missing s
            V1Cache.from_dict(config_dict).to_dict()
