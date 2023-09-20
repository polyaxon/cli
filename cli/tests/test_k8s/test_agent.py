import pytest

from mock import MagicMock, patch

from polyaxon._k8s.agent.agent import Agent
from polyaxon._k8s.executor.executor import Executor
from polyaxon._runner.agent.client import AgentClient
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.agent_mark
class TestAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    @patch("polyaxon._runner.agent.sync_agent.BaseSyncAgent._enter")
    def test_init_agent_component(self, register):
        agent = Agent(owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval is None
        assert isinstance(agent.executor, Executor)
        assert isinstance(agent.client, AgentClient)
        assert register.call_count == 0

    @patch("polyaxon._sdk.api.AgentsV1Api.sync_agent")
    @patch("polyaxon._sdk.api.AgentsV1Api.create_agent_status")
    @patch("polyaxon._sdk.api.AgentsV1Api.get_agent_state")
    @patch("polyaxon._sdk.api.AgentsV1Api.get_agent")
    @patch("polyaxon._k8s.executor.executor.Executor.manager")
    def test_init_agent(
        self, _, get_agent, get_agent_state, create_agent_status, sync_agent
    ):
        get_agent.return_value = MagicMock(status=None, live_state=1)
        get_agent_state.return_value = MagicMock(status=None, live_state=1)
        agent = Agent(owner="foo", agent_uuid="uuid")
        agent.executor.manager.get_version.return_value = {}
        assert agent.sleep_interval is None
        assert agent.executor is not None
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 0
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 0
        assert sync_agent.call_count == 0
        assert agent.executor.manager.get_version.call_count == 0

        agent._enter()
        assert agent.sleep_interval is None
        assert agent.executor is not None
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 1
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 1
        assert sync_agent.call_count == 1
        assert agent.executor.manager.get_version.call_count == 1
