import pytest

from polyaxon._flow import V1Operation
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._utils.fixtures import set_build_fixture
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestBuildsFixtures(BaseTestCase):
    def test_build_fixture(self):
        config = {
            "version": 1.1,
            "kind": "operation",
            "component": {
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "test"},
                },
            },
        }
        config = set_build_fixture(config, "test")
        assert V1Operation.read(config).to_dict() == config
