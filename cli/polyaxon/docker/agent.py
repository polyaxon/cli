from polyaxon.docker.executor import Executor
from polyaxon.runner.agent import BaseAgent


class Agent(BaseAgent):
    EXECUTOR = Executor
