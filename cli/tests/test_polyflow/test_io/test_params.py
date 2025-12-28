import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow.params import V1Param, is_short_form_param, normalize_param_value
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.polyflow_mark
class TestShortFormParams(BaseTestCase):
    """Tests for short-form param parsing feature (GitHub issue #895)."""

    def test_is_short_form_param_primitives(self):
        """Test that primitive values are detected as short-form."""
        # Integers
        assert is_short_form_param(32) is True
        assert is_short_form_param(0) is True
        assert is_short_form_param(-1) is True

        # Floats
        assert is_short_form_param(0.8) is True
        assert is_short_form_param(3.14) is True

        # Strings
        assert is_short_form_param("adam") is True
        assert is_short_form_param("") is True

        # Booleans
        assert is_short_form_param(True) is True
        assert is_short_form_param(False) is True

        # None
        assert is_short_form_param(None) is True

    def test_is_short_form_param_collections(self):
        """Test that collections without V1Param keys are detected as short-form."""
        # Lists
        assert is_short_form_param([1, 2, 3]) is True
        assert is_short_form_param(["a", "b", "c"]) is True
        assert is_short_form_param([]) is True

        # Dicts without V1Param keys
        assert is_short_form_param({"key1": "val1", "key2": "val2"}) is True
        assert is_short_form_param({"optimizer": "adam", "lr": 0.001}) is True

        # Empty dict is treated as full-form for backward compatibility
        assert is_short_form_param({}) is False

    def test_is_short_form_param_full_form(self):
        """Test that full-form V1Param dicts are NOT detected as short-form."""
        # Dicts with 'value' key
        assert is_short_form_param({"value": 32}) is False
        assert is_short_form_param({"value": "adam"}) is False
        assert is_short_form_param({"value": None}) is False

        # Dicts with 'ref' key
        assert (
            is_short_form_param({"value": "outputs.path", "ref": "ops.upstream"})
            is False
        )

        # Dicts with other V1Param keys
        assert is_short_form_param({"value": "data.csv", "toInit": True}) is False
        assert is_short_form_param({"value": "data.csv", "to_init": True}) is False
        assert is_short_form_param({"value": "env_val", "toEnv": "MY_VAR"}) is False
        assert is_short_form_param({"value": "env_val", "to_env": "MY_VAR"}) is False
        assert is_short_form_param({"contextOnly": True, "value": {}}) is False
        assert is_short_form_param({"context_only": True, "value": {}}) is False
        assert is_short_form_param({"connection": "my-conn", "value": "path"}) is False

    def test_normalize_param_value_short_form(self):
        """Test normalization of short-form values to full-form."""
        # Primitives
        assert normalize_param_value(32) == {"value": 32}
        assert normalize_param_value("adam") == {"value": "adam"}
        assert normalize_param_value(0.8) == {"value": 0.8}
        assert normalize_param_value(True) == {"value": True}
        assert normalize_param_value(None) == {"value": None}

        # Collections
        assert normalize_param_value([1, 2, 3]) == {"value": [1, 2, 3]}
        assert normalize_param_value({"key": "val"}) == {"value": {"key": "val"}}

    def test_normalize_param_value_full_form(self):
        """Test that full-form values are returned as-is."""
        # Already full-form - should not be wrapped
        full_form = {"value": 32}
        assert normalize_param_value(full_form) == full_form

        full_form_with_ref = {"value": "outputs.path", "ref": "ops.upstream"}
        assert normalize_param_value(full_form_with_ref) == full_form_with_ref

    def test_v1param_from_dict_short_form_primitives(self):
        """Test V1Param.from_dict with short-form primitive values."""
        # Integer
        param = V1Param.read(32)
        assert param.value == 32
        assert param.is_literal is True

        # Float
        param = V1Param.read(0.8)
        assert param.value == 0.8
        assert param.is_literal is True

        # String
        param = V1Param.read("adam")
        assert param.value == "adam"
        assert param.is_literal is True

        # Boolean
        param = V1Param.read(True)
        assert param.value is True
        assert param.is_literal is True

    def test_v1param_from_dict_short_form_collections(self):
        """Test V1Param.from_dict with short-form collection values."""
        # List
        param = V1Param.read([1, 2, 3])
        assert param.value == [1, 2, 3]
        assert param.is_literal is True

        # Dict (without V1Param keys)
        param = V1Param.read({"key1": "val1", "key2": "val2"})
        assert param.value == {"key1": "val1", "key2": "val2"}
        assert param.is_literal is True

    def test_v1param_from_dict_full_form_still_works(self):
        """Test that full-form V1Param.from_dict still works correctly."""
        # Full-form with value
        param = V1Param.read({"value": 32})
        assert param.value == 32
        assert param.is_literal is True

        # Full-form with ref
        param = V1Param.read({"value": "outputs.path", "ref": "ops.upstream"})
        assert param.value == "outputs.path"
        assert param.ref == "ops.upstream"
        assert param.is_literal is False
        assert param.is_ref is True

        # Full-form with toInit
        param = V1Param.read({"value": "data.csv", "toInit": True})
        assert param.value == "data.csv"
        assert param.to_init is True


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
        # ref without value should fail (ref is a V1Param key, so it's full-form)
        with self.assertRaises(ValidationError):
            V1Param.from_dict({"ref": "test"})
        with self.assertRaises(ValidationError):
            V1Param.from_dict({"connection": "test", "search": {"query": "test"}})

    def test_short_form_dict_without_v1param_keys(self):
        # A dict without V1Param keys is now valid as a short-form value
        # (the value becomes {"value": {"search": {"query": "test"}}})
        param = V1Param.read({"search": {"query": "test"}})
        assert param.value == {"search": {"query": "test"}}
        assert param.is_literal is True

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
