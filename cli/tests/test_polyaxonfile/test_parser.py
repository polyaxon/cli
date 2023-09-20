import pytest

from polyaxon._polyaxonfile.specs.libs.parser import PolyaxonfileParser
from polyaxon._utils.test_utils import BaseTestCase


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
