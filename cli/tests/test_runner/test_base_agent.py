import pytest

from mock import MagicMock, patch

from polyaxon.runner.agent.client import AgentClient
from polyaxon.runner.agent.sync_agent import BaseSyncAgent
from polyaxon.utils.test_utils import BaseTestCase


class DummyAgent(BaseSyncAgent):
    EXECUTOR = MagicMock


@pytest.mark.agent_mark
class TestBaseSyncAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    @patch("polyaxon.runner.agent.sync_agent.BaseSyncAgent._check_status")
    @patch("polyaxon.sdk.api.AgentsV1Api.sync_agent")
    @patch("polyaxon.sdk.api.AgentsV1Api.create_agent_status")
    @patch("polyaxon.sdk.api.AgentsV1Api.get_agent_state")
    @patch("polyaxon.sdk.api.AgentsV1Api.get_agent")
    def test_init_base_agent(
        self, get_agent, get_agent_state, create_agent_status, sync_agent, agent_check
    ):
        agent = DummyAgent()
        assert agent.sleep_interval is None
        assert agent.client.owner is None
        assert agent.client.agent_uuid is None
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 0
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 0
        assert sync_agent.call_count == 0
        assert agent.executor.manager.get_version.call_count == 0
        assert agent_check.call_count == 0

        agent._enter()
        assert agent.sleep_interval is None
        assert agent.client.owner is None
        assert agent.client.agent_uuid is None
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 0
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 0
        assert sync_agent.call_count == 0
        assert agent.executor.manager.get_version.call_count == 0
        assert agent_check.call_count == 0

        agent = DummyAgent(sleep_interval=2, owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval == 2
        assert agent.client.owner == "foo"
        assert agent.client.agent_uuid == "uuid"
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 0
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 0
        assert sync_agent.call_count == 0
        assert agent.executor.manager.get_version.call_count == 0
        assert agent_check.call_count == 0

        agent._enter()
        assert agent.sleep_interval == 2
        assert agent.client.owner == "foo"
        assert agent.client.agent_uuid == "uuid"
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 1
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 1
        assert sync_agent.call_count == 1
        assert agent.executor.manager.get_version.call_count == 1
        assert agent_check.call_count == 1

        get_agent.return_value = MagicMock(status=None, live_state=1)
        get_agent_state.return_value = MagicMock(status=None, live_state=1)
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval is None
        assert agent.client.owner == "foo"
        assert agent.client.agent_uuid == "uuid"
        assert agent.executor is not None
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 1
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 1
        assert sync_agent.call_count == 1
        assert agent.executor.manager.get_version.call_count == 0
        assert agent_check.call_count == 1

        agent._enter()
        assert agent.sleep_interval is None
        assert agent.client.owner == "foo"
        assert agent.client.agent_uuid == "uuid"
        assert agent.executor is not None
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 2
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 2
        assert sync_agent.call_count == 2
        assert agent.executor.manager.get_version.call_count == 1
        assert agent_check.call_count == 2

    @patch("polyaxon.runner.agent.sync_agent.BaseSyncAgent._enter")
    def test_init_agent_component(self, register):
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval is None
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert register.call_count == 0

        agent._enter()
        assert agent.sleep_interval is None
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert register.call_count == 1
