from collections import OrderedDict
import pytest
from unittest.mock import patch

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict
from polyaxon import types
from polyaxon._flow.io import V1IO
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonValidationError


@pytest.mark.polyflow_mark
class TestV1IO(BaseTestCase):
    def test_unvalued_non_flag_io_skips_value_validation(self):
        with patch("polyaxon._flow.io.io.validate_io") as validate:
            for is_optional in (None, False, True):
                for is_flag in (None, False):
                    values = {
                        "name": "input1",
                        "type": "int",
                        "value": None,
                        "is_optional": is_optional,
                        "is_flag": is_flag,
                    }
                    for config in (values, V1IO.model_construct(**values)):
                        assert V1IO.validate_io(config) is config
            validate.assert_not_called()

    def test_falsy_defaults_still_validate_on_model_revalidation(self):
        for io_type, value, is_list in (
            ("bool", False, False),
            ("int", 0, False),
            ("str", "", False),
            ("int", [], True),
            ("dict", {}, False),
        ):
            values = {
                "name": "input1",
                "type": io_type,
                "value": value,
                "is_list": is_list,
                "is_optional": False,
            }
            for config in (values, V1IO.model_construct(**values)):
                with self.subTest(io_type=io_type, value=value):
                    with self.assertRaises(ValueError):
                        V1IO.validate_io(config)

    def test_unvalued_flags_still_validate_on_model_revalidation(self):
        for io_type in (None, "int", "str"):
            values = {"name": "input1", "type": io_type, "is_flag": True}
            for config in (values, V1IO.model_construct(**values)):
                with self.assertRaisesRegex(ValueError, "cannot be a flag"):
                    V1IO.validate_io(config)

    def test_wrong_io_config(self):
        # No name
        with self.assertRaises(ValidationError):
            V1IO.from_dict({})

    def test_unsupported_config_type_does_not_until_type_check(self):
        io = V1IO.from_dict({"name": "input1", "type": "something"})
        assert io.type == "something"

    def test_wrong_io_config_default(self):
        with self.assertRaises(ValidationError):
            V1IO.from_dict({"name": "input1", "type": "float", "value": "foo"})

        with self.assertRaises(ValidationError):
            V1IO.from_dict({"name": "input1", "type": types.GCS, "value": 234})

    def test_wrong_io_config_flag(self):
        with self.assertRaises(ValidationError):
            V1IO.from_dict({"name": "input1", "type": types.S3, "isFlag": True})

        with self.assertRaises(ValidationError):
            V1IO.from_dict({"name": "input1", "type": "float", "isFlag": True})

    def test_io_name_blacklist(self):
        config_dict = {"name": "params"}
        with self.assertRaises(ValidationError):
            V1IO.from_dict(config_dict)

        config_dict = {"name": "globals"}
        with self.assertRaises(ValidationError):
            V1IO.from_dict(config_dict)

        config_dict = {"name": "connections"}
        with self.assertRaises(ValidationError):
            V1IO.from_dict(config_dict)

    def test_io_config_optionals(self):
        config_dict = {"name": "input1"}
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        assert config.is_optional is None

    def test_io_config_desc(self):
        # test desc
        config_dict = {"name": "input1", "description": "some text"}
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_iotype_backwards_compatibility(self):
        with self.assertRaises(ValidationError):
            V1IO(name="test", iotype="bool")
        config1 = V1IO(name="test", type="bool")
        assert config1.to_dict() == {"name": "test", "type": "bool"}

    def test_io_config_types(self):
        config_dict = {"name": "input1", "description": "some text", "type": "int"}
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        expected_repr = OrderedDict((("name", "input1"), ("type", "int"), ("value", 3)))
        assert config.get_repr_from_value(3) == expected_repr
        assert config.get_repr() == OrderedDict((("name", "input1"), ("type", "int")))

        config_dict = {"name": "input1", "description": "some text", "type": types.S3}
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        expected_repr = OrderedDict(
            (("name", "input1"), ("type", types.S3), ("value", "s3://foo"))
        )
        assert config.get_repr_from_value("s3://foo") == expected_repr
        assert config.get_repr() == OrderedDict(
            (("name", "input1"), ("type", types.S3))
        )

    def test_io_config_default(self):
        config_dict = {
            "name": "input1",
            "description": "some text",
            "type": "bool",
            "isOptional": True,
            "value": True,
        }
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        expected_repr = OrderedDict(
            (("name", "input1"), ("type", "bool"), ("value", True))
        )
        assert config.get_repr_from_value(None) == expected_repr
        assert config.get_repr() == expected_repr

        config_dict = {
            "name": "input1",
            "description": "some text",
            "type": "float",
            "isOptional": True,
            "value": 3.4,
        }
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        expected_repr = OrderedDict(
            (("name", "input1"), ("type", "float"), ("value", 3.4))
        )
        assert config.get_repr_from_value(None) == expected_repr
        assert config.get_repr() == expected_repr

    def test_io_config_default_and_required(self):
        config_dict = {
            "name": "input1",
            "description": "some text",
            "type": "bool",
            "value": True,
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict = {
            "name": "input1",
            "description": "some text",
            "type": "str",
            "value": "foo",
        }
        expected_config_dict = {
            "name": "input1",
            "description": "some text",
            "type": "str",
            "value": "foo",
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        expected_config = V1IO.from_dict(expected_config_dict)
        assert_equal_dict(config.to_dict(), expected_config.to_dict())

    def test_io_config_default_is_implicitly_optional(self):
        config_dicts = [
            {"name": "null-input", "type": "str", "value": None},
            {"name": "str-input", "type": "str", "value": "foo"},
            {"name": "empty-str-input", "type": "str", "value": ""},
            {"name": "int-input", "type": "int", "value": 1},
            {"name": "zero-input", "type": "int", "value": 0},
            {"name": "true-input", "type": "bool", "value": True},
            {"name": "false-input", "type": "bool", "value": False},
            {
                "name": "list-input",
                "type": "int",
                "isList": True,
                "value": [1],
            },
            {
                "name": "empty-list-input",
                "type": "int",
                "isList": True,
                "value": [],
            },
            {"name": "dict-input", "type": "dict", "value": {"foo": "bar"}},
            {"name": "empty-dict-input", "type": "dict", "value": {}},
        ]

        for config_dict in config_dicts:
            with self.subTest(config_dict=config_dict):
                config = V1IO.from_dict(config_dict)
                assert config.is_optional is True
                assert config.value == config_dict["value"]

                expected = {**config_dict, "isOptional": True}
                if config_dict["value"] is None:
                    expected.pop("value")
                assert_equal_dict(config.to_dict(), expected)

    def test_io_config_default_cannot_be_explicitly_required(self):
        values = (None, "foo", "", 1, 0, True, False, [1], [], {"foo": "bar"}, {})
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    V1IO.from_dict(
                        {"name": "input1", "value": value, "isOptional": False}
                    )

    def test_io_config_required(self):
        config_dict = {
            "name": "input1",
            "description": "some text",
            "type": "float",
            "isOptional": False,
        }
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        expected_repr = OrderedDict(
            (("name", "input1"), ("type", "float"), ("value", 1.1))
        )
        assert config.get_repr_from_value(1.1) == expected_repr
        assert config.get_repr() == OrderedDict((("name", "input1"), ("type", "float")))

    def test_io_config_flag(self):
        config_dict = {
            "name": "input1",
            "description": "some text",
            "type": "bool",
            "isFlag": True,
        }
        config = V1IO.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
        expected_repr = OrderedDict(
            (("name", "input1"), ("type", "bool"), ("value", False))
        )
        assert config.get_repr_from_value(False) == expected_repr

    def test_value_non_typed_input(self):
        config_dict = {"name": "input1"}
        config = V1IO.from_dict(config_dict)
        assert config.validate_value("foo") == "foo"
        assert config.validate_value(1) == 1
        assert config.validate_value(True) is True

        expected_repr = OrderedDict((("name", "input1"), ("value", "foo")))
        assert config.get_repr_from_value("foo") == expected_repr
        assert config.get_repr() == OrderedDict(name="input1")

    def test_value_typed_input(self):
        config_dict = {"name": "input1", "type": "bool"}
        config = V1IO.from_dict(config_dict)
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("foo")
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(None)

        assert config.validate_value(1) is True
        assert config.validate_value("1") is True
        assert config.validate_value(True) is True

    def test_value_typed_input_with_default(self):
        config_dict = {
            "name": "input1",
            "type": "int",
            "value": 12,
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("foo")

        assert config.validate_value(1) == 1
        assert config.validate_value(0) == 0
        assert config.validate_value(-1) == -1
        assert config.validate_value(None) == 12
        expected_repr = OrderedDict(
            (("name", "input1"), ("type", "int"), ("value", 12))
        )
        assert config.get_repr_from_value(None) == expected_repr
        assert config.get_repr() == expected_repr
