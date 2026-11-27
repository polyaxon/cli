import pytest
import sys

from polyaxon._config.parser import ConfigParser
from polyaxon._flow.io import V1IO, V1Validation
from polyaxon._schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1EventType,
    V1FileType,
    V1GitType,
    V1TensorboardType,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonValidationError


@pytest.mark.polyflow_mark
class TestV1Validation(BaseTestCase):
    def test_options_validation_backwards_compatibility(self):
        config1 = V1IO(name="test", type="str", options=["foo", "bar"])
        assert config1.to_dict() == {
            "name": "test",
            "type": "str",
            "validation": {"options": ["foo", "bar"]},
        }
        assert config1.validation.to_dict() == {"options": ["foo", "bar"]}

    def test_delay_validation_backwards_compatibility(self):
        config1 = V1IO(name="test", type="str", delay_validation=True)
        assert config1.to_dict() == {
            "name": "test",
            "type": "str",
            "validation": {"delay": True},
        }
        assert config1.validation.to_dict() == {"delay": True}

    def test_backwards_compatibility(self):
        config1 = V1IO(
            name="test",
            type="str",
            options=["foo", "bar"],
            delay_validation=False,
            validation=V1Validation(min_length=2),
        )
        assert config1.to_dict() == {
            "name": "test",
            "type": "str",
            "validation": {"options": ["foo", "bar"], "delay": False, "minLength": 2},
        }
        assert config1.validation.to_dict() == {
            "options": ["foo", "bar"],
            "delay": False,
            "minLength": 2,
        }

        config1 = V1IO.from_dict(
            {
                "name": "test",
                "type": "str",
                "options": ["foo", "bar"],
                "delay_validation": False,
                "validation": {
                    "options": ["foo", "bar"],
                    "delay": False,
                    "minLength": 2,
                },
            }
        )
        assert config1.to_dict() == {
            "name": "test",
            "type": "str",
            "validation": {"options": ["foo", "bar"], "delay": False, "minLength": 2},
        }
        assert config1.validation.to_dict() == {
            "options": ["foo", "bar"],
            "delay": False,
            "minLength": 2,
        }

    def test_validate_gt(self):
        config_dict = {"name": "input1", "type": "int", "value": 3, "isOptional": True}
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == 3

        config_dict = {
            "name": "input1",
            "type": "int",
            "value": 3,
            "isOptional": True,
            "validation": {"gt": 2},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(2)
        assert config.validate_value(None) == 3

    def test_validate_gt_list(self):
        config_dict = {
            "name": "input1",
            "type": "List[int]",
            "value": [3, 4],
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value([4]) == [4]
        assert config.validate_value([3, 2, 4]) == [3, 2, 4]
        assert config.validate_value(None) == [3, 4]

        config_dict = {
            "name": "input1",
            "type": "List[int]",
            "value": [3, 4],
            "isOptional": True,
            "validation": {"gt": 2},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value([4]) == [4]
        assert config.validate_value([32, 5]) == [32, 5]
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value([2])
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value([1, 50])
        assert config.validate_value(None) == [3, 4]

    def test_validate_nested_type_expressions(self):
        for type_, value in (
            ("List[Dict[str, Optional[StrictInt]]]", [{"count": 3}, {"count": None}]),
            ("List[Optional[Callable[[str], int]]]", [len, None]),
        ):
            with self.subTest(type=type_):
                config = V1IO(name="input1", type=type_)
                assert config.validate_value(value) == value

    def test_validate_gt_dict(self):
        config_dict = {
            "name": "input1",
            "type": "Dict[str, int]",
            "value": {"a": 3, "b": 4},
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value({"b": 4}) == {"b": 4}
        assert config.validate_value({"c": 2, "d": 12}) == {"c": 2, "d": 12}
        assert config.validate_value(None) == {"a": 3, "b": 4}

        config_dict = {
            "name": "input1",
            "type": "Dict[str, int]",
            "value": {"a": 3, "b": 4},
            "isOptional": True,
            "validation": {"gt": 2},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value({"b": 4}) == {"b": 4}
        assert config.validate_value({"c": 32, "d": 5}) == {"c": 32, "d": 5}
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"f": 2})
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"f": 1, "y": 50})
        assert config.validate_value(None) == {"a": 3, "b": 4}

    def test_validate_ge(self):
        config_dict = {"name": "input1", "type": "int", "value": 3, "isOptional": True}
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == 3

        config_dict = {
            "name": "input1",
            "type": "int",
            "value": 3,
            "isOptional": True,
            "validation": {"ge": 2},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(1)
        assert config.validate_value(None) == 3

    def test_validate_lt(self):
        config_dict = {"name": "input1", "type": "int", "value": 3, "isOptional": True}
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == 3

        config_dict = {
            "name": "input1",
            "type": "int",
            "value": 3,
            "isOptional": True,
            "validation": {"lt": 4},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(4)
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == 3

    def test_validate_le(self):
        config_dict = {"name": "input1", "type": "int", "value": 3, "isOptional": True}
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == 3

        config_dict = {
            "name": "input1",
            "type": "int",
            "value": 3,
            "isOptional": True,
            "validation": {"le": 4},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(5)
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == 3

    def test_validate_multiple_of(self):
        config_dict = {"name": "input1", "type": "int", "value": -6, "isOptional": True}
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(4) == 4
        assert config.validate_value(3) == 3
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == -6

        config_dict = {
            "name": "input1",
            "type": "int",
            "value": -6,
            "isOptional": True,
            "validation": {"multipleOf": 2},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(5)
        assert config.validate_value(4) == 4
        assert config.validate_value(2) == 2
        assert config.validate_value(None) == -6

    def test_validate_min_digits(self):
        config_dict = {
            "name": "input1",
            "type": "float",
            "value": 3.141,
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(3.14159265359) == 3.14159265359
        assert config.validate_value(3.1415926535) == 3.1415926535
        assert config.validate_value(3.141592) == 3.141592
        assert config.validate_value(None) == 3.141

        config_dict = {
            "name": "input1",
            "type": "float",
            "value": 3.141,
            "isOptional": True,
            "validation": {"minDigits": 4},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(3.1)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(31)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(3.14)
        assert config.validate_value(3.1415920) == 3.141592
        assert config.validate_value(3.141592) == 3.141592
        assert config.validate_value(3.141592) == 3.141592
        assert config.validate_value(None) == 3.141

    def test_validate_max_digits(self):
        config_dict = {
            "name": "input1",
            "type": "float",
            "value": 3.141,
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(3.14159265359) == 3.14159265359
        assert config.validate_value(3.1415926535) == 3.1415926535
        assert config.validate_value(3.141592) == 3.141592
        assert config.validate_value(None) == 3.141

        config_dict = {
            "name": "input1",
            "type": "float",
            "value": 3.141,
            "isOptional": True,
            "validation": {"maxDigits": 7},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(3.14159265359)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(3.1415926535)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(32.141592)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(324141592)
        assert config.validate_value(33.4159200) == 33.41592
        assert config.validate_value(33.41592) == 33.41592
        assert config.validate_value(3.141592) == 3.141592
        assert config.validate_value(314159) == 314159
        assert config.validate_value(None) == 3.141

    def test_validate_decimal_places(self):
        config_dict = {
            "name": "input1",
            "type": "float",
            "value": 3.141,
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(3.14159265359) == 3.14159265359
        assert config.validate_value(3.1415926535) == 3.1415926535
        assert config.validate_value(3.141592) == 3.141592
        assert config.validate_value(None) == 3.141

        config_dict = {
            "name": "input1",
            "type": "float",
            "value": 3.141,
            "isOptional": True,
            "validation": {"decimalPlaces": 3},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(3.14159265359)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(3.1415926535)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(3.141592)
        with self.assertRaises(PolyaxonValidationError):
            assert config.validate_value(3.1412)
        assert config.validate_value(3.1) == 3.1
        assert config.validate_value(3.14) == 3.14
        assert config.validate_value(3.141) == 3.141
        assert config.validate_value(None) == 3.141

    def test_validate_regex(self):
        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("bar") == "bar"
        assert config.validate_value(None) == "foo"

        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
            "validation": {"regex": "^foo$"},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("bar")
        assert config.validate_value("foo") == "foo"
        assert config.validate_value(None) == "foo"

    def test_validate_min_length(self):
        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("bar") == "bar"
        assert config.validate_value(None) == "foo"

        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
            "validation": {"minLength": 3},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("fo")
        assert config.validate_value("foo") == "foo"
        assert config.validate_value(None) == "foo"

    def test_validate_max_length(self):
        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("bar") == "bar"
        assert config.validate_value(None) == "foo"

        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
            "validation": {"maxLength": 3},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("fooo")
        assert config.validate_value("foo") == "foo"
        assert config.validate_value(None) == "foo"

    def test_validate_contains(self):
        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("bar") == "bar"
        assert config.validate_value(None) == "foo"

        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
            "validation": {"contains": "oo"},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("bar")
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("boo") == "boo"
        assert config.validate_value(None) == "foo"

    def test_validate_excludes(self):
        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("bar") == "bar"
        assert config.validate_value(None) == "foo"

        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "phone",
            "isOptional": True,
            "validation": {"excludes": "oo"},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("foo")
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("boo")
        assert config.validate_value("bar") == "bar"
        assert config.validate_value("mp12") == "mp12"
        assert config.validate_value(None) == "phone"

    def test_validate_options(self):
        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        config.validate_value("boo") == "boo"
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("bar") == "bar"
        assert config.validate_value(None) == "foo"

        config_dict = {
            "name": "input1",
            "type": "str",
            "value": "foo",
            "isOptional": True,
            "validation": {"options": ["foo", "bar"]},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value("boo")
        assert config.validate_value("foo") == "foo"
        assert config.validate_value("bar") == "bar"
        assert config.validate_value(None) == "foo"

    def test_validation_min_items(self):
        config_dict = {
            "name": "input1",
            "type": "list",
            "value": ["foo", "bar"],
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(["foo", "bar"]) == ["foo", "bar"]
        assert config.validate_value(["foo"]) == ["foo"]
        assert config.validate_value(None) == ["foo", "bar"]

        config_dict = {
            "name": "input1",
            "type": "list",
            "value": ["foo", "bar"],
            "isOptional": True,
            "validation": {"minItems": 2},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(["foo"])
        assert config.validate_value(["foo", "bar"]) == ["foo", "bar"]
        assert config.validate_value(["foo", "bar", "boo"]) == ["foo", "bar", "boo"]
        assert config.validate_value(None) == ["foo", "bar"]

    def test_validation_max_items(self):
        config_dict = {
            "name": "input1",
            "type": "list",
            "value": ["foo", "bar"],
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value(["foo", "bar"]) == ["foo", "bar"]
        assert config.validate_value(["foo"]) == ["foo"]
        assert config.validate_value(None) == ["foo", "bar"]

        config_dict = {
            "name": "input1",
            "type": "list",
            "value": ["foo", "bar"],
            "isOptional": True,
            "validation": {"maxItems": 2},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value(["foo", "bar", "boo"])
        assert config.validate_value(["foo", "bar"]) == ["foo", "bar"]
        assert config.validate_value(["foo"]) == ["foo"]
        assert config.validate_value(None) == ["foo", "bar"]

    def test_validate_keys(self):
        config_dict = {
            "name": "input1",
            "type": "dict",
            "value": {"foo": "bar"},
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value({"foo": "bar"}) == {"foo": "bar"}
        assert config.validate_value({"foo": "bar", "boo": "bar"}) == {
            "foo": "bar",
            "boo": "bar",
        }
        assert config.validate_value(None) == {"foo": "bar"}

        config_dict = {
            "name": "input1",
            "type": "dict",
            "value": {"foo": "1", "boo": "2"},
            "isOptional": True,
            "validation": {"keys": ["foo", "boo"]},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"boo": "bar"})
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"moo": "bar", "boo": "bar"})
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"foo": "bar"})
        assert config.validate_value({"foo": "bar", "boo": "bar"}) == {
            "foo": "bar",
            "boo": "bar",
        }
        assert config.validate_value(None) == {"foo": "1", "boo": "2"}

    def test_validate_keys_contains(self):
        config_dict = {
            "name": "input1",
            "type": "dict",
            "value": {"foo": "bar"},
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value({"foo": "bar"}) == {"foo": "bar"}
        assert config.validate_value({"foo": "bar", "boo": "bar"}) == {
            "foo": "bar",
            "boo": "bar",
        }
        assert config.validate_value(None) == {"foo": "bar"}

        config_dict = {
            "name": "input1",
            "type": "dict",
            "value": {"foo": "bar"},
            "isOptional": True,
            "validation": {"containsKeys": ["foo"]},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"boo": "bar"})
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"moo": "bar", "boo": "bar"})
        assert config.validate_value({"foo": "bar", "boo": "bar"}) == {
            "foo": "bar",
            "boo": "bar",
        }
        assert config.validate_value({"foo": "bar"}) == {"foo": "bar"}
        assert config.validate_value(None) == {"foo": "bar"}

    def test_validate_keys_excludes(self):
        config_dict = {
            "name": "input1",
            "type": "dict",
            "value": {"foo": "bar"},
            "isOptional": True,
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        assert config.validate_value({"foo": "bar"}) == {"foo": "bar"}
        assert config.validate_value({"foo": "bar", "boo": "bar"}) == {
            "foo": "bar",
            "boo": "bar",
        }
        assert config.validate_value(None) == {"foo": "bar"}

        config_dict = {
            "name": "input1",
            "type": "dict",
            "value": {"foo": "bar"},
            "isOptional": True,
            "validation": {"excludesKeys": ["boo"]},
        }
        config = V1IO.from_dict(config_dict)
        assert config.to_dict() == config_dict
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"boo": "bar"})
        with self.assertRaises(PolyaxonValidationError):
            config.validate_value({"moo": "bar", "boo": "bar"})
        assert config.validate_value({"foo": "bar", "moo": "bar"}) == {
            "foo": "bar",
            "moo": "bar",
        }
        assert config.validate_value({"foo": "bar"}) == {"foo": "bar"}
        assert config.validate_value(None) == {"foo": "bar"}


@pytest.mark.polyflow_mark
class TestV1IOTypeExpressions(BaseTestCase):
    def test_supported_type_expressions(self):
        for type_, value, expected in (
            ("int", 12, 12),
            ("str", "foo", "foo"),
            ("float", 1.5, 1.5),
            ("bool", True, True),
            ("dict", {"a": 1}, {"a": 1}),
            ("list", [1, 2], [1, 2]),
            ("Any", {"a": [1]}, {"a": [1]}),
            ("any", "foo", "foo"),
            ("StrictInt", 3, 3),
            # Loadable types JSON-decode string values first.
            ("StrictStr", '"foo"', "foo"),
            ("List[str]", ["a"], ["a"]),
            ("List[int]", [1, 2], [1, 2]),
            ("Dict[str, int]", {"a": 1}, {"a": 1}),
            ("Dict[str, Any]", {"a": [1]}, {"a": [1]}),
            ("Optional[int]", 3, 3),
            ("Union[int, str]", 3, 3),
            ("Tuple[int, int]", [1, 2], (1, 2)),
            ("int | None", 3, 3),
            ("object", {"a": 1}, {"a": 1}),
            ("Dict[str, object]", {"a": 1, "b": [2]}, {"a": 1, "b": [2]}),
            ("List[object]", [1, "x"], [1, "x"]),
            ("Type[int]", int, int),
            ("List['int']", [1], [1]),
            ("Dict['str', 'int']", {"a": 1}, {"a": 1}),
        ):
            with self.subTest(type=type_):
                config = V1IO(name="input1", type=type_, is_optional=True)
                assert config.validate_value(value) == expected

    def test_polyaxon_types_in_type_expressions(self):
        config = V1IO(name="input1", type="List[V1GitType]")
        result = config.validate_value([{"url": "https://github.com/a/b"}])
        assert result[0].url == "https://github.com/a/b"

    def test_type_expression_does_not_run_code(self):
        probe = "_plx_type_probe"
        self.addCleanup(sys.modules.pop, probe, None)
        call = f"__import__('sys').modules.__setitem__('{probe}', 1) or int"
        quoted_call = call.replace("'", '"')
        for type_, value in ((f"({call})", 3), (f"List['{quoted_call}']", [1])):
            with self.subTest(type=type_):
                with self.assertRaises(PolyaxonValidationError):
                    V1IO(name="input1", type=type_).validate_value(value)
                assert probe not in sys.modules

    def test_short_type_aliases(self):
        config = V1IO(name="input1", type="List[GitType]")
        result = config.validate_value([{"url": "https://github.com/a/b"}])
        assert result[0].url == "https://github.com/a/b"
        for alias, cls in (
            ("FileType", V1FileType),
            ("DockerfileType", V1DockerfileType),
            ("TensorboardType", V1TensorboardType),
            ("GitType", V1GitType),
            ("EventType", V1EventType),
            ("ArtifactsType", V1ArtifactsType),
        ):
            with self.subTest(alias=alias):
                assert ConfigParser.resolve_type(alias) is cls

    def test_malformed_type_expressions(self):
        for type_, kwargs, value in (
            ("(int, str)", {"is_list": True}, [1]),
            ("(int, str)", {}, 1),
            ("[int]", {}, [1]),
            ("...", {}, 1),
            ("...", {"is_list": True}, [1]),
            ("Optional", {"is_list": True}, [1]),
            ("List[[int]]", {}, [1]),
            ("Optional[[int]]", {}, 1),
        ):
            with self.subTest(type=type_, **kwargs):
                with self.assertRaisesRegex(PolyaxonValidationError, "input1"):
                    V1IO(name="input1", type=type_, **kwargs).validate_value(value)

    def test_missing_value_does_not_resolve_type(self):
        type_ = "Literal['a']"
        for kwargs in ({}, {"is_list": True}):
            with self.subTest(**kwargs):
                config = V1IO(name="input1", type=type_, is_optional=True, **kwargs)
                assert config.validate_value(None) is None
        with self.assertRaisesRegex(PolyaxonValidationError, "No value was provided"):
            V1IO(name="input1", type=type_).validate_value(None)

    def test_type_expression_rejects_non_type_syntax(self):
        for type_, value in (("int.__class__", int), ("(lambda: int)()", 3)):
            with self.subTest(type=type_):
                with self.assertRaises(PolyaxonValidationError):
                    V1IO(name="input1", type=type_).validate_value(value)
