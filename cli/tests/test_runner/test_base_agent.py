import pytest

from mock import MagicMock, patch

from polyaxon.client import PolyaxonClient
from polyaxon.runner.agent import BaseAgent
from polyaxon.utils.test_utils import BaseTestCase


class DummyAgent(BaseAgent):
    EXECUTOR = MagicMock


@pytest.mark.agent_mark
class TestBaseAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    @patch("polyaxon.runner.agent.BaseAgent._check_status")
    @patch("polyaxon.sdk.api.AgentsV1Api.sync_agent")
    @patch("polyaxon.sdk.api.AgentsV1Api.create_agent_status")
    @patch("polyaxon.sdk.api.AgentsV1Api.get_agent_state")
    @patch("polyaxon.sdk.api.AgentsV1Api.get_agent")
    def test_init_base_agent(
        self, get_agent, get_agent_state, create_agent_status, sync_agent, agent_check
    ):
        agent = DummyAgent()
        assert agent.sleep_interval is None
        assert agent.owner is None
        assert agent.agent_uuid is None
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, PolyaxonClient)
        assert get_agent.call_count == 1
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 1
        assert sync_agent.call_count == 1
        assert agent.executor.manager.get_version.call_count == 1
        assert agent_check.call_count == 1

        agent = DummyAgent(sleep_interval=2, owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval == 2
        assert agent.owner == "foo"
        assert agent.agent_uuid == "uuid"
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, PolyaxonClient)
        assert get_agent.call_count == 2
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 2
        assert sync_agent.call_count == 2
        assert agent.executor.manager.get_version.call_count == 1
        assert agent_check.call_count == 2

        get_agent.return_value = MagicMock(status=None, live_state=1)
        get_agent_state.return_value = MagicMock(status=None, live_state=1)
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval is None
        assert agent.executor is not None
        assert isinstance(agent.client, PolyaxonClient)
        assert get_agent.call_count == 3
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 3
        assert sync_agent.call_count == 3
        assert agent.executor.manager.get_version.call_count == 1
        assert agent_check.call_count == 3

    @patch("polyaxon.runner.agent.BaseAgent._register")
    def test_init_agent_component(self, register):
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        assert agent.sleep_interval is None
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, PolyaxonClient)
        assert register.call_count == 1
