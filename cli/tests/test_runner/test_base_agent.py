import pytest

from polyaxon.client import PolyaxonClient
from polyaxon.runner.agent import BaseAgent
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.agent_mark
class TestBaseAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    def test_init_base_agent(self):
        agent = BaseAgent()
        assert agent.sleep_interval is None
        assert agent.executor is None
        assert isinstance(agent.client, PolyaxonClient)

        agent = BaseAgent(sleep_interval=2)
        assert agent.sleep_interval == 2
        assert agent.executor is None
        assert isinstance(agent.client, PolyaxonClient)
