from polyaxon._k8s.executor.async_executor import AsyncExecutor
from polyaxon._runner.agent.async_agent import BaseAsyncAgent


class AsyncAgent(BaseAsyncAgent):
    EXECUTOR = AsyncExecutor
