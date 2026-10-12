import pytest

from polyaxon._polyaxonfile.params import parse_env, parse_ports
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError


@pytest.mark.polyaxonfile_mark
class TestParams(BaseTestCase):
    def test_parse_env(self):
        assert parse_env(["TOKEN=a=b", "EMPTY="]) == {"TOKEN": "a=b", "EMPTY": ""}
        for values in (["A"], ["=x"], ["A=1", "A=2"]):
            with self.subTest(values=values):
                with self.assertRaises(PolyaxonfileError):
                    parse_env(values, is_cli=False)

    def test_parse_ports(self):
        assert parse_ports(["80", "9999,8888", " 443 , 8443 ", "80"]) == [
            80,
            9999,
            8888,
            443,
            8443,
            80,
        ]
        for values in (["abc"], ["80,"], ["80,,443"], ["-1"], ["+80"], ["8.5"], ["٨٠"]):
            with self.subTest(values=values):
                with self.assertRaises(PolyaxonfileError):
                    parse_ports(values, is_cli=False)
