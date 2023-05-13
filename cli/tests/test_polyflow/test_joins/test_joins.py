import pytest

from clipped.utils.assertions import assert_equal_dict

from polyaxon.polyflow import V1Join
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.hooks_mark
class TestJoinsConfigs(BaseTestCase):
    def test_join(self):
        config_dict = {
            "query": "metrics.a: < 21",
            "sort": "-inputs.name1",
            "params": {
                "a": {"value": "inputs.a"},
                "outputs": {"value": "outputs", "contextOnly": True},
            },
        }
        config = V1Join.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict = {
            "query": "metrics.a: < 21",
            "sort": "-inputs.name1",
            "limit": 2,
            "params": {
                "output1": {"value": "outputs.output1", "connection": "test"},
            },
        }
        config = V1Join.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict = {
            "query": "status: succeeded|failed",
            "params": {
                "events": {"value": "artifact.metric1.events", "toInit": True},
            },
        }
        config = V1Join.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_join_with_refs(self):
        config_dict = {
            "query": "metrics.metric: > {{ metric_level }}",
            "sort": "-metrics.metric",
            "limit": "{{ top }}",
            "params": {
                "metrics": {"value": "outputs.metric"},
            },
        }
        config = V1Join.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
