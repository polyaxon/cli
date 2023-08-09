import pytest

from polyaxon.exceptions import PolyaxonValidationError
from polyaxon.polyflow.io import V1IO, V1Validation
from polyaxon.utils.test_utils import BaseTestCase


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
