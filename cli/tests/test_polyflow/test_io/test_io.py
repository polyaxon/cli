import pytest
import uuid

from collections import OrderedDict

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict
from clipped.utils.json import orjson_dumps

from polyaxon import types
from polyaxon._flow.io import V1IO
from polyaxon._flow.params import ParamSpec, V1Param
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonValidationError


@pytest.mark.polyflow_mark
class TestV1IO(BaseTestCase):
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
        with self.assertRaises(ValidationError):
            V1IO.from_dict(config_dict)

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
