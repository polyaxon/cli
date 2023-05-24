import pytest

from mock import MagicMock, patch

from polyaxon.client import PolyaxonClient
from polyaxon.k8s.agent import Agent
from polyaxon.k8s.executor.executor import Executor
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.agent_mark
class TestAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    @patch("polyaxon.k8s.agent.Agent._register")
    def test_init_agent_component(self, register):
        agent = Agent(owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval is None
        assert isinstance(agent.executor, Executor)
        assert isinstance(agent.client, PolyaxonClient)
        assert register.call_count == 1

    @patch("polyaxon.sdk.api.AgentsV1Api.sync_agent")
    @patch("polyaxon.sdk.api.AgentsV1Api.create_agent_status")
    @patch("polyaxon.sdk.api.AgentsV1Api.get_agent_state")
    @patch("polyaxon.sdk.api.AgentsV1Api.get_agent")
    @patch("polyaxon.k8s.agent.Executor")
    def test_init_agent(
        self, _, get_agent, get_agent_state, create_agent_status, sync_agent
    ):
        get_agent.return_value = MagicMock(status=None, live_state=1)
        get_agent_state.return_value = MagicMock(status=None, live_state=1)
        agent = Agent(owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval is None
        assert agent.executor is not None
        assert isinstance(agent.client, PolyaxonClient)
        assert get_agent.call_count == 1
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 1
        assert sync_agent.call_count == 1
        assert agent.executor.manager.get_version.call_count == 1
