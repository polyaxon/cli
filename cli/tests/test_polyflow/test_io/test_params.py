import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow.params import V1Param
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.polyflow_mark
class TestV1Params(BaseTestCase):
    def test_missing_value_param_config(self):
        param = V1Param.from_dict({})
        assert param.value is None

        param = V1Param.from_dict({"value": None})
        assert param.value is None

    def test_wrong_param_with_ref_and_search(self):
        with self.assertRaises(ValidationError):
            V1Param.from_dict(
                {"value": "something", "ref": "test", "search": {"query": "test"}}
            )

    def test_wrong_param_without_value(self):
        with self.assertRaises(ValidationError):
            V1Param.from_dict({"ref": "test"})
        with self.assertRaises(ValidationError):
            V1Param.from_dict({"search": {"query": "test"}})

    def test_wrong_param_value_type(self):
        with self.assertRaises(ValidationError):
            V1Param.from_dict({"ref": "test", "value": 12})
        with self.assertRaises(ValidationError):
            V1Param.from_dict({"search": {"query": "test"}, "value": {"foo": "bar"}})

    def test_param_config_with_value(self):
        config_dict = {"value": None}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is True
        assert config.is_ref is False

        config_dict = {"value": "string_value"}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is True
        assert config.is_ref is False

        config_dict = {"value": 234}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is True
        assert config.is_ref is False

        config_dict = {"value": 23.4}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is True
        assert config.is_ref is False

        config_dict = {"value": {"key": "value"}}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is True
        assert config.is_ref is False

        config_dict = {"value": ["value1", "value2"]}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is True
        assert config.is_ref is False

    def test_param_ref(self):
        config_dict = {"value": "outputs", "ref": "ops.A"}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is False
        assert config.is_ref is True

        config_dict = {"value": "outputs.output1", "ref": "ops.A"}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is False
        assert config.is_ref is True

        config_dict = {
            "value": "artifact.metric_events",
            "ref": "runs.0de53b5bf8b04a219d12a39c6b92bcce",
        }
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is False
        assert config.is_ref is True

        config_dict = {"value": "input.param1", "ref": "dag"}
        config = V1Param.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_literal is False
        assert config.is_ref is True
