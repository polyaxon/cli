from polyaxon.k8s.executor.executor import Executor
from polyaxon.runner.agent.sync_agent import BaseSyncAgent


class Agent(BaseSyncAgent):
    EXECUTOR = Executor
