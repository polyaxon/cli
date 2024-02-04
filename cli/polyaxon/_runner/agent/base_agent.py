import time
import traceback

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Tuple, Type

from clipped.utils.tz import now

from polyaxon import settings
from polyaxon._auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon._connections import V1Connection
from polyaxon._constants.globals import DEFAULT
from polyaxon._runner.agent.client import AgentClient
from polyaxon._runner.executor import BaseExecutor
from polyaxon._schemas.checks import ChecksConfig
from polyaxon._schemas.lifecycle import LiveState, V1Statuses
from polyaxon.client import V1AgentStateResponse
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.logger import logger


class BaseAgent:
    EXECUTOR: Type[BaseExecutor]
    HEALTH_FILE = "/tmp/.healthz"
    SLEEP_STOP_TIME = 60 * 5
    SLEEP_ARCHIVED_TIME = 60 * 60
    SLEEP_AGENT_DATA_COLLECT_TIME = 60 * 30
    IS_ASYNC = False

    def __init__(
        self,
        owner: Optional[str] = None,
        agent_uuid: Optional[str] = None,
        max_interval: Optional[int] = None,
    ):
        self.max_interval = 6 if agent_uuid else 4
        if max_interval:
            self.max_interval = max(max_interval, 3)
        if not agent_uuid and not owner:
            owner = DEFAULT
        self.executor = None
        self._default_auth = bool(agent_uuid)
        self._executor_refreshed_at = now()
        self._graceful_shutdown = False
        self._last_reconciled_at = now()
        self.client = AgentClient(
            owner=owner, agent_uuid=agent_uuid, is_async=self.IS_ASYNC
        )
        self.executor = self.EXECUTOR()
        self.content = settings.AGENT_CONFIG.to_json()

    def sync(self):
        raise NotImplementedError

    def reconcile(self):
        raise NotImplementedError

    def cron(self):
        return self.client.cron_agent()

    def collect_agent_data(self):
        logger.info("Collecting agent data.")
        self._last_reconciled_at = now()
        try:
            return self.client.collect_agent_data(
                namespace=settings.CLIENT_CONFIG.namespace
            )
        except Exception as e:
            logger.warning(
                "Agent failed to collect agent data: {}\n"
                "Retrying ...".format(repr(e))
            )

    def sync_compatible_updates(self, compatible_updates: Dict):
        if compatible_updates and settings.AGENT_CONFIG:
            init = compatible_updates.get("init")
            if init and settings.AGENT_CONFIG.init:
                init = V1PolyaxonInitContainer.from_dict(init)
                settings.AGENT_CONFIG.init = settings.AGENT_CONFIG.init.patch(init)

            sidecar = compatible_updates.get("sidecar")
            if sidecar and settings.AGENT_CONFIG.sidecar:
                sidecar = V1PolyaxonSidecarContainer.from_dict(sidecar)
                settings.AGENT_CONFIG.sidecar = settings.AGENT_CONFIG.sidecar.patch(
                    sidecar
                )
            connections = compatible_updates.get("connections")
            if connections:
                settings.AGENT_CONFIG.connections = [
                    V1Connection.from_dict(c) for c in connections
                ]

            self.content = settings.AGENT_CONFIG.to_json()
            return self.sync()

    @classmethod
    def get_healthz_config(cls) -> Optional[ChecksConfig]:
        try:
            return ChecksConfig.read(cls.HEALTH_FILE, config_type=".json")
        except Exception:  # noqa
            return None

    @classmethod
    def ping(cls):
        if not settings.AGENT_CONFIG.enable_health_checks:
            return
        ChecksConfig.init_file(cls.HEALTH_FILE)
        config = cls.get_healthz_config()
        if config:
            config.last_check = now()
            config.write(cls.HEALTH_FILE, mode=config._WRITE_MODE)

    @classmethod
    def pong(cls, interval: int = 15) -> bool:
        config = cls.get_healthz_config()
        if not config:
            return False
        return not config.should_check(interval=interval)

    def refresh_executor(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def end(self, sleep: Optional[int] = None):
        self._graceful_shutdown = True
        if sleep:
            time.sleep(sleep)
        else:
            logger.info("Agent is shutting down.")

    def _check_status(self, agent_state):
        if agent_state.status == V1Statuses.STOPPED:
            logger.warning(
                "Agent has been stopped from the platform,"
                "but the deployment is still running."
                "Please either set the agent to starting or teardown the agent deployment."
            )
            return self.end(sleep=self.SLEEP_STOP_TIME)
        elif agent_state.live_state < LiveState.LIVE:
            logger.warning(
                "Agent has been archived from the platform,"
                "but the deployment is still running."
                "Please either restore the agent or teardown the agent deployment."
            )
            return self.end(sleep=self.SLEEP_ARCHIVED_TIME)

    def process(self, pool: "ThreadPoolExecutor") -> V1AgentStateResponse:
        raise NotImplementedError

    def make_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
        default_auth: bool = False,
    ) -> Optional[Any]:
        try:
            return self.executor.make_and_convert(
                owner_name=owner_name,
                project_name=project_name,
                run_uuid=run_uuid,
                run_name=run_name,
                content=content,
                default_auth=default_auth,
            )
        except PolyaxonConverterError as e:
            logger.info(
                "Run could not be cleaned. Agent failed converting run manifest: {}\n{}".format(
                    repr(e), traceback.format_exc()
                )
            )
        except Exception as e:
            logger.info(
                "Agent failed during compilation with unknown exception: {}\n{}".format(
                    repr(e), traceback.format_exc()
                )
            )
        return None

    def prepare_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
    ) -> Optional[Any]:
        raise NotImplementedError

    def submit_run(self, run_data: Tuple[str, str, str, str, str]):
        raise NotImplementedError

    def make_and_create_run(
        self, run_data: Tuple[str, str, str, str, str], default_auth: bool = False
    ):
        raise NotImplementedError

    def apply_run(self, run_data: Tuple[str, str, str, str, str]):
        raise NotImplementedError

    def check_run(self, run_data: Tuple[str, str, str]):
        raise NotImplementedError

    def stop_run(self, run_data: Tuple[str, str, str]):
        raise NotImplementedError

    def delete_run(self, run_data: Tuple[str, str, str, str, str]):
        raise NotImplementedError

    def clean_run(self, run_uuid: str, run_kind: str, namespace: str = None):
        raise NotImplementedError
