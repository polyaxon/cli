from polyaxon.k8s.executor.async_executor import AsyncExecutor
from polyaxon.runner.agent.async_agent import BaseAsyncAgent


class AsyncAgent(BaseAsyncAgent):
    EXECUTOR = AsyncExecutor
