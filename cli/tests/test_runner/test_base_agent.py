from mock import MagicMock, patch
import pytest

from polyaxon import settings
from polyaxon._constants.globals import DEFAULT
from polyaxon._runner.agent.client import AgentClient, AsyncAgentClient
from polyaxon._runner.agent.sync_agent import BaseSyncAgent
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonAgentError


class DummyAgent(BaseSyncAgent):
    EXECUTOR = MagicMock


@pytest.mark.agent_mark
class TestBaseSyncAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    @patch("polyaxon._runner.agent.sync_agent.BaseSyncAgent._check_status")
    @patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.check_agent_connection")
    @patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.sync_agent")
    @patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.create_agent_status")
    @patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.get_agent_state")
    @patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.get_agent")
    @patch("polyaxon._k8s.executor.executor.Executor.manager")
    def test_init_base_agent(
        self,
        _,
        get_agent,
        get_agent_state,
        create_agent_status,
        sync_agent,
        check_agent_connection,
        agent_check,
    ):
        check_agent_connection.return_value = {"status": "passed", "results": []}
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
        assert check_agent_connection.call_count == 1
        check_agent_connection.assert_called_with(
            namespace=settings.CLIENT_CONFIG.namespace,
            owner="foo",
            uuid="uuid",
            body={},
        )
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
        assert check_agent_connection.call_count == 2
        assert agent.executor.manager.get_version.call_count == 1
        assert agent_check.call_count == 2

    def test_connection_failure_blocks_sync_agent_startup(self):
        result = {"status": "failed", "results": []}
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        agent.client = MagicMock()
        agent.client._is_managed = True
        agent.client.get_info.return_value = MagicMock(status=None, live_state=1)
        agent.client.check_agent_connections.return_value = result
        agent.sync = MagicMock()

        with pytest.raises(PolyaxonAgentError, match="Agent connection check failed"):
            agent.__enter__()

        agent.client.check_agent_connections.assert_called_once_with(
            namespace=settings.CLIENT_CONFIG.namespace
        )
        agent.sync.assert_not_called()
        agent.client.log_agent_running.assert_not_called()
        agent.client.log_agent_failed.assert_called_once_with(
            message="Agent connection check failed: {}".format(result),
            reason="AgentConnectionCheck",
            meta_info={"connection_check": result},
        )
        agent.client.close.assert_called_once()

    def test_connection_request_failure_blocks_sync_agent_startup(self):
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        agent.client = MagicMock()
        agent.client._is_managed = True
        agent.client.get_info.return_value = MagicMock(status=None, live_state=1)
        agent.client.check_agent_connections.side_effect = TimeoutError()
        agent.sync = MagicMock()

        with pytest.raises(
            PolyaxonAgentError, match="Agent connection check request failed"
        ):
            agent.__enter__()

        failure = agent.client.log_agent_failed.call_args.kwargs
        assert failure["reason"] == "AgentConnectionCheck"
        check = failure["meta_info"]["connection_check"]
        assert check["status"] == "failed"
        assert check["error"]["code"] == "connection_check_request_failed"
        assert check["error"]["exception"] == "TimeoutError"
        agent.sync.assert_not_called()
        agent.client.log_agent_running.assert_not_called()
        agent.client.close.assert_called_once()

    def test_invalid_connection_response_blocks_sync_agent_startup(self):
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        agent.client = MagicMock()
        agent.client._is_managed = True
        agent.client.get_info.return_value = MagicMock(status=None, live_state=1)
        agent.client.check_agent_connections.return_value = None
        agent.sync = MagicMock()

        with pytest.raises(PolyaxonAgentError, match="returned an invalid response"):
            agent.__enter__()

        agent.client.log_agent_failed.assert_called_once_with(
            message="Agent connection check returned an invalid response.",
            reason="AgentConnectionCheck",
            meta_info={
                "connection_check": {
                    "status": "failed",
                    "error": {
                        "code": "connection_check_invalid_response",
                        "exception": "PolyaxonAgentError",
                    },
                }
            },
        )
        agent.sync.assert_not_called()
        agent.client.log_agent_running.assert_not_called()
        agent.client.close.assert_called_once()

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
        client = AsyncAgentClient(owner="foo", agent_uuid="uuid")

        _ = client.internal_client

        client_cls.assert_called_once_with(is_async=True, is_internal=True)

    def test_sync_agent_exit_closes_client_in_finally(self):
        agent = DummyAgent(owner="foo", agent_uuid="uuid")
        agent.client = MagicMock()
        agent._exit = MagicMock(side_effect=RuntimeError("exit failed"))

        with pytest.raises(RuntimeError):
            agent.__exit__(None, None, None)

        agent.client.close.assert_called_once()
