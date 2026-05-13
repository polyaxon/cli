from mock import MagicMock, patch
import pytest

from polyaxon._constants.globals import DEFAULT
from polyaxon._runner.agent.client import AgentClient
from polyaxon._runner.agent.sync_agent import BaseSyncAgent
from polyaxon._utils.test_utils import BaseTestCase


class DummyAgent(BaseSyncAgent):
    EXECUTOR = MagicMock


@pytest.mark.agent_mark
class TestBaseSyncAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    @patch("polyaxon._runner.agent.sync_agent.BaseSyncAgent._check_status")
    @patch("polyaxon._sdk.api.AgentsV1Api.sync_agent")
    @patch("polyaxon._sdk.api.AgentsV1Api.create_agent_status")
    @patch("polyaxon._sdk.api.AgentsV1Api.get_agent_state")
    @patch("polyaxon._sdk.api.AgentsV1Api.get_agent")
    @patch("polyaxon._k8s.executor.executor.Executor.manager")
    def test_init_base_agent(
        self,
        _,
        get_agent,
        get_agent_state,
        create_agent_status,
        sync_agent,
        agent_check,
    ):
        agent = DummyAgent()
        agent.executor.manager.get_version.return_value = {}
        assert agent.max_interval == 4
        assert agent.client.owner == DEFAULT
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
        assert agent.max_interval == 4
        assert agent.client.owner == DEFAULT
        assert agent.client.agent_uuid is None
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert get_agent.call_count == 0
        assert get_agent_state.call_count == 0
        assert create_agent_status.call_count == 0
        assert sync_agent.call_count == 0
        assert agent.executor.manager.get_version.call_count == 0
        assert agent_check.call_count == 0

        agent = DummyAgent(max_interval=2, owner="foo", agent_uuid="uuid")
        agent.executor.manager.get_version.return_value = {}
        assert agent.max_interval == 3
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
        assert agent.max_interval == 3
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
        agent.executor.manager.get_version.return_value = {}
        assert agent.max_interval == 6
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
        assert agent.max_interval == 6
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

    @patch("polyaxon._runner.agent.sync_agent.BaseSyncAgent._enter")
    def test_init_agent_component(self, register):
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        assert agent.max_interval == 6
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert register.call_count == 0

        agent._enter()
        assert agent.max_interval == 6
        assert isinstance(agent.executor, MagicMock)
        assert isinstance(agent.client, AgentClient)
        assert register.call_count == 1

    def test_agent_client_uses_internal_client_for_collect_agent_data(self):
        public_client = MagicMock()
        internal_client = MagicMock()
        client = AgentClient(
            owner="foo",
            agent_uuid="uuid",
            client=public_client,
            internal_client=internal_client,
        )

        client.collect_agent_data(namespace="default")

        assert public_client.agents_v1.collect_agent_data.call_count == 0
        internal_client.agents_v1.collect_agent_data.assert_called_once_with(
            owner="foo",
            uuid="uuid",
            namespace="default",
        )

    @patch("polyaxon._runner.agent.client.PolyaxonClient")
    def test_agent_client_creates_internal_client_with_internal_mode(self, client_cls):
        client = AgentClient(owner="foo", agent_uuid="uuid", is_async=True)

        _ = client.internal_client

        client_cls.assert_called_once_with(is_async=True, is_internal=True)
