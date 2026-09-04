from mock import MagicMock, patch
import pytest

from polyaxon import settings
from polyaxon._k8s.agent.async_agent import AsyncAgent
from polyaxon._k8s.executor.async_executor import AsyncExecutor
from polyaxon._runner.agent.client import AsyncAgentClient
from polyaxon._utils.test_utils import AsyncMock, patch_settings
from polyaxon.exceptions import ApiException, PolyaxonAgentError


@pytest.mark.agent_mark
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
@patch(
    "polyaxon._runner.agent.async_agent.BaseAsyncAgent._enter", new_callable=AsyncMock
)
async def test_init_agent_component(register):
    patch_settings()
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    assert agent.max_interval == 6
    assert isinstance(agent.executor, AsyncExecutor)
    assert isinstance(agent.client, AsyncAgentClient)
    assert register.call_count == 0


@pytest.mark.agent_mark
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
@patch(
    "polyaxon._sdk.api.agents_v1_api.AgentsV1Api.check_agent_connection",
    new_callable=AsyncMock,
)
@patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.sync_agent", new_callable=AsyncMock)
@patch(
    "polyaxon._sdk.api.agents_v1_api.AgentsV1Api.create_agent_status",
    new_callable=AsyncMock,
)
@patch(
    "polyaxon._sdk.api.agents_v1_api.AgentsV1Api.get_agent_state",
    new_callable=AsyncMock,
)
@patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.get_agent", new_callable=AsyncMock)
@patch(
    "polyaxon._k8s.executor.async_executor.AsyncExecutor.manager",
    new_callable=AsyncMock,
)
async def test_init_agent(
    _,
    get_agent,
    get_agent_state,
    create_agent_status,
    sync_agent,
    check_agent_connection,
):
    patch_settings()
    get_agent.return_value = MagicMock(status=None, live_state=1)
    check_agent_connection.return_value = {"status": "passed", "results": []}
    get_agent_state.return_value = MagicMock(status=None, live_state=1)
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    agent.executor.manager.get_version.return_value = {}
    assert agent.max_interval == 6
    assert agent.executor is not None
    assert isinstance(agent.client, AsyncAgentClient)
    assert get_agent.call_count == 0
    assert get_agent_state.call_count == 0
    assert create_agent_status.call_count == 0
    assert sync_agent.call_count == 0
    assert check_agent_connection.call_count == 0
    assert agent.executor.manager.get_version.call_count == 0

    await agent._enter()
    assert agent.max_interval == 6
    assert agent.executor is not None
    assert isinstance(agent.client, AsyncAgentClient)
    assert get_agent.call_count == 1
    assert get_agent_state.call_count == 0
    assert create_agent_status.call_count == 1
    assert sync_agent.call_count == 1
    assert check_agent_connection.call_count == 1
    assert agent.executor.manager.get_version.call_count == 1


@pytest.mark.agent_mark
@pytest.mark.asyncio
async def test_async_agent_connection_failure_blocks_startup():
    patch_settings()
    settings.CLIENT_CONFIG.namespace = "client-namespace"
    result = {"status": "failed", "results": []}
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    agent.executor = MagicMock()
    agent.executor.refresh = AsyncMock()
    agent.client = MagicMock()
    agent.client._is_managed = True
    agent.client.get_info = AsyncMock(return_value=MagicMock(status=None, live_state=1))
    agent.client.check_agent_connections = AsyncMock(return_value=result)
    agent.client.log_agent_failed = AsyncMock()
    agent.client.log_agent_running = AsyncMock()
    agent.client.aclose = AsyncMock()
    agent.sync = AsyncMock()

    with pytest.raises(PolyaxonAgentError, match="Agent connection check failed"):
        await agent.__aenter__()

    agent.client.check_agent_connections.assert_called_once_with(
        namespace="client-namespace"
    )
    agent.executor.refresh.assert_not_called()
    agent.sync.assert_not_called()
    agent.client.log_agent_running.assert_not_called()
    agent.client.log_agent_failed.assert_called_once_with(
        message="Agent connection check failed: {}".format(result),
        reason="AgentConnectionCheck",
        meta_info={"connection_check": result},
    )
    agent.client.aclose.assert_called_once()


@pytest.mark.agent_mark
@pytest.mark.asyncio
async def test_async_agent_connection_request_failure_reports_and_closes():
    patch_settings()
    settings.CLIENT_CONFIG.namespace = "client-namespace"
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    agent.executor = MagicMock()
    agent.executor.refresh = AsyncMock()
    agent.client = MagicMock()
    agent.client._is_managed = True
    agent.client.get_info = AsyncMock(return_value=MagicMock(status=None, live_state=1))
    agent.client.check_agent_connections = AsyncMock(side_effect=TimeoutError())
    agent.client.log_agent_failed = AsyncMock()
    agent.client.aclose = AsyncMock()
    agent.sync = AsyncMock()

    with pytest.raises(
        PolyaxonAgentError, match="Agent connection check request failed"
    ):
        await agent.__aenter__()

    failure = agent.client.log_agent_failed.call_args.kwargs
    assert failure["reason"] == "AgentConnectionCheck"
    assert failure["meta_info"]["connection_check"]["status"] == "failed"
    error = failure["meta_info"]["connection_check"]["error"]
    assert error["code"] == "connection_check_request_failed"
    assert error["exception"] == "TimeoutError"
    agent.executor.refresh.assert_not_called()
    agent.sync.assert_not_called()
    agent.client.aclose.assert_called_once()


@pytest.mark.agent_mark
@pytest.mark.asyncio
async def test_async_agent_aexit_closes_client_in_finally():
    patch_settings()
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    agent.client = MagicMock()
    agent.client.aclose = AsyncMock()
    agent._exit = AsyncMock(side_effect=RuntimeError("exit failed"))

    with pytest.raises(RuntimeError):
        await agent.__aexit__(None, None, None)

    agent.client.aclose.assert_called_once()


@pytest.mark.agent_mark
@pytest.mark.asyncio
async def test_async_agent_reconcile_continues_after_collect_failure(caplog):
    patch_settings()
    settings.CLIENT_CONFIG.namespace = "client-namespace"
    settings.AGENT_CONFIG.namespace = "agent-namespace"
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    agent.client = MagicMock()
    agent.client.collect_agent_data = AsyncMock(
        side_effect=ApiException(status=500, reason="failure")
    )
    agent.client.reconcile_agent = AsyncMock()
    agent.executor = MagicMock()
    agent.executor.list_ops = AsyncMock(return_value=[])

    await agent.reconcile()

    agent.client.collect_agent_data.assert_called_once_with(
        namespace="client-namespace",
    )
    agent.executor.list_ops.assert_called_once_with(namespace="agent-namespace")
    assert "Agent failed to collect agent data" in caplog.text
    assert "status=500" in caplog.text
    assert "reason=failure" in caplog.text
