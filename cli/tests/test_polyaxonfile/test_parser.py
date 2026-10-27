import pytest

from polyaxon._polyaxonfile.specs.libs.parser import (
    ContainerText,
    PolyaxonfileParser,
    TextValue,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonSchemaError


@pytest.mark.polyaxonfile_mark
class TestPolyaxonfileParser(BaseTestCase):
    def test_parse_base_expressions(self):
        data = [
            1,
            10.0,
            [1, 1],
            (1, 1),
            "string",
            ["str1", "str2"],
            {1: 2, "a": "a", "dict": {1: 1}},
        ]

        parser = PolyaxonfileParser()
        for d in data:
            assert d == parser.parse_expression(d, {})

    def test_parse_context_expression(self):
        parser = PolyaxonfileParser()
        assert parser.parse_expression("{{ something }}", {}) == ""
        assert parser.parse_expression("{{ something }}", {"something": 1}) == 1

    def test_parse_nested_keys_and_values(self):
        expression = {"{{ key }}": ["{{ value }}", {"nested": "{{ value }}"}]}
        context = {"key": "result", "value": "{{ target }}", "target": 7}
        assert PolyaxonfileParser.parse_expression(expression, context) == {
            "result": [7, {"nested": 7}]
        }

    def test_second_pass_rejects_forbidden_attributes(self):
        context = {"value": "{{ ''.__class__ }}"}
        with pytest.raises(PolyaxonSchemaError):
            PolyaxonfileParser.parse_expression("{{ value }}", context)

    def test_typed_text_renders_only_once(self):
        context = {"value": "{{ target }}", "target": 7}
        assert PolyaxonfileParser.parse_expression("{{ value }}", context) == 7
        assert PolyaxonfileParser.parse_expression(
            TextValue("{{ value }}"), context
        ) == ("{{ target }}")
        assert (
            PolyaxonfileParser.parse_expression(
                ContainerText("{{ missing }}"), {"missing": None}
            )
            is None
        )

    def test_recursive_template_cycle_is_rejected(self):
        context = {"a": "{{ b }}", "b": "{{ a }}"}
        with pytest.raises(PolyaxonSchemaError, match="maximum rendering passes"):
            PolyaxonfileParser.parse_expression("{{ a }}", context)

    def test_recursive_render_pass_limit(self):
        context = {f"p{i}": f"{{{{ p{i + 1} }}}}" for i in range(7)}
        context["p7"] = "done"
        assert PolyaxonfileParser.parse_expression("{{ p0 }}", context) == "done"

        context["p7"] = "{{ p8 }}"
        context["p8"] = "done"
        with pytest.raises(PolyaxonSchemaError, match="maximum rendering passes"):
            PolyaxonfileParser.parse_expression("{{ p0 }}", context)
