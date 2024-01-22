import traceback

from typing import Dict, Optional

from polyaxon._schemas.lifecycle import V1StatusCondition, V1Statuses
from polyaxon.client import PolyaxonClient, V1Agent, V1AgentStateResponse
from polyaxon.logger import logger


class AgentClient:
    def __init__(
        self,
        owner: Optional[str] = None,
        agent_uuid: Optional[str] = None,
        client: Optional[PolyaxonClient] = None,
        is_async: bool = False,
    ):
        self.owner = owner
        self.agent_uuid = agent_uuid
        self.is_async = is_async
        self._client = client

    @property
    def client(self):
        if self._client:
            return self._client
        self._client = PolyaxonClient(is_async=self.is_async)
        return self._client

    @property
    def _is_managed(self):
        return self.owner is not None and self.agent_uuid is not None

    def get_info(self) -> V1Agent:
        return self.client.agents_v1.get_agent(owner=self.owner, uuid=self.agent_uuid)

    def get_state(self) -> V1AgentStateResponse:
        if self._is_managed:
            return self.client.agents_v1.get_agent_state(
                owner=self.owner, uuid=self.agent_uuid
            )
        return self.client.agents_v1.get_global_state(owner=self.owner)

    def log_agent_status(
        self, status: str, reason: Optional[str] = None, message: Optional[str] = None
    ):
        if not self._is_managed:
            return
        status_condition = V1StatusCondition.get_condition(
            type=status, status=True, reason=reason, message=message
        )
        return self.client.agents_v1.create_agent_status(
            owner=self.owner,
            uuid=self.agent_uuid,
            body={"condition": status_condition},
        )

    def sync_agent(self, agent: V1Agent):
        return self.client.agents_v1.sync_agent(
            owner=self.owner,
            agent_uuid=self.agent_uuid,
            body=agent,
        )

    def cron_agent(self):
        return self.client.agents_v1.cron_agent(owner=self.owner, _request_timeout=10)

    def collect_agent_data(self, namespace: str):
        return self.client.internal_agents_v1.collect_agent_data(
            owner=self.owner,
            uuid=self.agent_uuid,
            namespace=namespace,
        )

    def reconcile_agent(self, reconcile: Dict):
        return self.client.agents_v1.reconcile_agent(
            owner=self.owner,
            uuid=self.agent_uuid,
            body={"reconcile": reconcile},
        )

    def log_agent_running(self):
        return self.log_agent_status(status=V1Statuses.RUNNING, reason="AgentLogger")

    def log_agent_failed(self, message=None):
        return self.log_agent_status(
            status=V1Statuses.FAILED, reason="AgentLogger", message=message
        )

    def log_agent_warning(self):
        return self.log_agent_status(
            status=V1Statuses.WARNING,
            reason="AgentLogger",
            message="The agent was interrupted, please check your deployment.",
        )

    def log_run_failed(
        self,
        run_owner: str,
        run_project: str,
        run_uuid: str,
        exc: Exception,
        message: Optional[str] = None,
    ):
        message = message or "Agent failed deploying run.\n"
        message += "error: {}\n{}".format(repr(exc), traceback.format_exc())
        logger.warning(message)
        return self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.FAILED,
            reason="AgentLogger",
            message=message,
        )

    def log_run_stopped(self, run_owner: str, run_project: str, run_uuid: str):
        message = "Run was not found. The agent assumed it was already stopped."
        logger.warning(message)
        return self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.STOPPED,
            reason="AgentLogger",
            message=message,
        )

    def log_run_scheduled(self, run_owner: str, run_project: str, run_uuid: str):
        message = "Run was scheduled by the agent."
        logger.info(message)
        return self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.SCHEDULED,
            reason="AgentLogger",
            message=message,
        )

    def log_run_running(self, run_owner: str, run_project: str, run_uuid: str):
        message = "Run changes were applied by the agent."
        logger.info(message)
        return self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.RUNNING,
            reason="AgentLogger",
            message=message,
        )

    def log_run_status(
        self,
        run_owner: str,
        run_project: str,
        run_uuid: str,
        status: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
    ):
        status_condition = V1StatusCondition.get_condition(
            type=status, status=True, reason=reason, message=message
        )
        return self.client.runs_v1.create_run_status(
            owner=run_owner,
            project=run_project,
            uuid=run_uuid,
            body={"condition": status_condition},
        )
