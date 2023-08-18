import pytest

from mock import patch
from unittest.mock import AsyncMock

from polyaxon.k8s.agent.async_agent import AsyncAgent
from polyaxon.k8s.executor.async_executor import AsyncExecutor
from polyaxon.runner.agent.client import AgentClient
from polyaxon.utils.test_utils import patch_settings


@pytest.mark.agent_mark
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
@patch(
    "polyaxon.runner.agent.async_agent.BaseAsyncAgent._enter", new_callable=AsyncMock
)
async def test_init_agent_component(register):
    patch_settings()
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    assert agent.sleep_interval is None
    assert isinstance(agent.executor, AsyncExecutor)
    assert isinstance(agent.client, AgentClient)
    assert register.call_count == 0


@pytest.mark.agent_mark
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
@patch("polyaxon.sdk.api.AgentsV1Api.sync_agent", new_callable=AsyncMock)
@patch("polyaxon.sdk.api.AgentsV1Api.create_agent_status", new_callable=AsyncMock)
@patch("polyaxon.sdk.api.AgentsV1Api.get_agent_state", new_callable=AsyncMock)
@patch("polyaxon.sdk.api.AgentsV1Api.get_agent", new_callable=AsyncMock)
@patch(
    "polyaxon.k8s.executor.async_executor.AsyncExecutor.manager", new_callable=AsyncMock
)
async def test_init_agent(
    _, get_agent, get_agent_state, create_agent_status, sync_agent
):
    patch_settings()
    get_agent.return_value = AsyncMock(status=None, live_state=1)
    get_agent_state.return_value = AsyncMock(status=None, live_state=1)
    agent = AsyncAgent(owner="foo", agent_uuid="uuid")
    agent.executor.manager.get_version.return_value = {}
    assert agent.sleep_interval is None
    assert agent.executor is not None
    assert isinstance(agent.client, AgentClient)
    assert get_agent.call_count == 0
    assert get_agent_state.call_count == 0
    assert create_agent_status.call_count == 0
    assert sync_agent.call_count == 0
    assert agent.executor.manager.get_version.call_count == 0

    await agent._enter()
    assert agent.sleep_interval is None
    assert agent.executor is not None
    assert isinstance(agent.client, AgentClient)
    assert get_agent.call_count == 1
    assert get_agent_state.call_count == 0
    assert create_agent_status.call_count == 1
    assert sync_agent.call_count == 1
    assert agent.executor.manager.get_version.call_count == 1
