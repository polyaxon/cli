#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import time
import traceback

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Tuple

from clipped.utils.enums import PEnum
from clipped.utils.tz import now
from clipped.utils.workers import exit_context, get_pool_workers, get_wait
from kubernetes.client.rest import ApiException

from polyaxon import live_state, settings
from polyaxon.client import PolyaxonClient
from polyaxon.env_vars.getters import get_run_info
from polyaxon.exceptions import PolypodException
from polyaxon.lifecycle import V1StatusCondition, V1Statuses
from polyaxon.logger import logger
from polyaxon.schemas.cli.checks_config import ChecksConfig
from polyaxon.schemas.responses.v1_agent import V1Agent
from polyaxon.schemas.responses.v1_agent_state_response import V1AgentStateResponse


class AgentKind(str, PEnum):
    K8S = "k8s"
    PROCESS = "process"
    DOCKER = "docker"


class BaseAgent:
    HEALTH_FILE = "/tmp/.healthz"
    SLEEP_STOP_TIME = 60 * 5
    SLEEP_ARCHIVED_TIME = 60 * 60

    def __init__(self, sleep_interval=None):
        self.sleep_interval = sleep_interval
        self.executor = None
        self._executor_refreshed_at = now()
        self.client = PolyaxonClient()
        self._graceful_shutdown = False
        self.content = settings.AGENT_CONFIG.to_json()

    def get_info(self) -> V1Agent:
        raise NotImplementedError

    def get_state(self) -> V1AgentStateResponse:
        raise NotImplementedError

    def sync_compatible_updates(self, compatible_updates: Dict):
        raise NotImplementedError

    @classmethod
    def get_healthz_config(cls) -> Optional[ChecksConfig]:
        try:
            return ChecksConfig.read(cls.HEALTH_FILE, config_type=".json")
        except Exception:  # noqa
            return None

    @classmethod
    def ping(cls):
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
        if (
            now() - self._executor_refreshed_at
        ).total_seconds() > settings.AGENT_CONFIG.get_executor_refresh_interval():
            logger.debug("Refreshing executor ... ")
            self.executor.refresh()
            self._executor_refreshed_at = now()

    def start(self):
        try:
            with exit_context() as exit_event:
                index = 0
                workers = get_pool_workers()

                with ThreadPoolExecutor(workers) as pool:
                    logger.debug("Thread pool Workers: {}".format(workers))
                    timeout = self.sleep_interval or get_wait(index)
                    while not exit_event.wait(timeout=timeout):
                        index += 1
                        self.refresh_executor()
                        agent_state = self.process(pool)
                        self._check_status(agent_state)
                        if agent_state.state.full:
                            index = 2
                        self.ping()
                        timeout = self.sleep_interval or get_wait(index)
                        logger.info("Sleeping for {} seconds".format(timeout))
        finally:
            self.end()

    def _check_status(self, agent_state):
        if agent_state.status == V1Statuses.STOPPED:
            print(
                "Agent has been stopped from the platform,"
                "but the deployment is still running."
                "Please either set the agent to starting or teardown the agent deployment."
            )
            self.end(sleep=self.SLEEP_STOP_TIME)
        elif agent_state.live_state < live_state.STATE_LIVE:
            print(
                "Agent has been archived from the platform,"
                "but the deployment is still running."
                "Please either restore the agent or teardown the agent deployment."
            )
            self.end(sleep=self.SLEEP_ARCHIVED_TIME)

    def end(self, sleep: Optional[int] = None):
        self._graceful_shutdown = True
        if sleep:
            time.sleep(sleep)
        else:
            logger.info("Agent is shutting down.")

    def process(self, pool: "ThreadPoolExecutor") -> V1AgentStateResponse:
        try:
            agent_state = self.get_state()
            if agent_state.compatible_updates:
                self.sync_compatible_updates(agent_state.compatible_updates)

            if agent_state:
                logger.info("Starting runs submission process.")
            else:
                logger.info("No state was found.")
                return V1AgentStateResponse.construct()

            state = agent_state.state
            if not state:
                return agent_state
            for run_data in state.schedules or []:
                pool.submit(self.submit_run, run_data)
            for run_data in state.queued or []:
                pool.submit(self.submit_run, run_data)
            for run_data in state.checks or []:
                pool.submit(self.check_run, run_data)
            for run_data in state.stopping or []:
                pool.submit(self.stop_run, run_data)
            for run_data in state.apply or []:
                pool.submit(self.apply_run, run_data)
            for run_data in state.deleting or []:
                pool.submit(self.delete_run, run_data)
            for run_data in state.hooks or []:
                pool.submit(self.make_and_create_run, run_data)
            for run_data in state.watchdogs or []:
                pool.submit(self.make_and_create_run, run_data)
            for run_data in state.tuners or []:
                pool.submit(self.make_and_create_run, run_data, True)
            return agent_state
        except Exception as exc:
            logger.error(exc)
            return V1AgentStateResponse.construct()

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
        self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.FAILED,
            reason="AgentLogger",
            message=message,
        )
        logger.warning(message)

    def log_run_stopped(self, run_owner: str, run_project: str, run_uuid: str):
        message = "Run was not found. The agent assumed it was already stopped."
        self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.STOPPED,
            reason="AgentLogger",
            message=message,
        )
        logger.warning(message)

    def log_run_scheduled(self, run_owner: str, run_project: str, run_uuid: str):
        message = "Run was scheduled by the agent."
        self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.SCHEDULED,
            reason="AgentLogger",
            message=message,
        )
        logger.info(message)

    def log_run_running(self, run_owner: str, run_project: str, run_uuid: str):
        message = "Run changes were applied by the agent."
        self.log_run_status(
            run_owner=run_owner,
            run_project=run_project,
            run_uuid=run_uuid,
            status=V1Statuses.RUNNING,
            reason="AgentLogger",
            message=message,
        )
        logger.info(message)

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
        self.client.runs_v1.create_run_status(
            owner=run_owner,
            project=run_project,
            uuid=run_uuid,
            body={"condition": status_condition},
            async_req=True,
        )

    def clean_run(self, run_uuid: str, run_kind: str):
        try:
            self.executor.clean(run_uuid=run_uuid, run_kind=run_kind)
            self.executor.stop(run_uuid=run_uuid, run_kind=run_kind)
        except ApiException as e:
            if e.status == 404:
                logger.info("Run does not exist.")
        except Exception as e:
            logger.info(
                "Run could not be cleaned: {}\n{}".format(
                    repr(e), traceback.format_exc()
                )
            )

    def _make_and_convert(
        self,
        owner_name: str,
        project_name: str,
        run_uuid: str,
        run_name: str,
        content: str,
        default_auth: bool = False,
    ):
        return None

    def make_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
        default_auth=False,
    ) -> Optional[Dict]:
        try:
            return self._make_and_convert(
                owner_name=owner_name,
                project_name=project_name,
                run_uuid=run_uuid,
                run_name=run_name,
                content=content,
                default_auth=default_auth,
            )
        except PolypodException as e:
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

    def _convert(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
        default_auth: bool,
        agent_content: Optional[str] = None,
    ):
        return None

    def prepare_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
    ) -> Optional[Dict]:
        try:
            return self._convert(
                owner_name=owner_name,
                project_name=project_name,
                run_name=run_name,
                run_uuid=run_uuid,
                content=content,
                default_auth=True,
                agent_content=self.content,
            )
        except PolypodException as e:
            self.log_run_failed(
                run_owner=owner_name,
                run_project=project_name,
                run_uuid=run_uuid,
                exc=e,
                message="Agent failed converting run manifest.\n",
            )
        except Exception as e:
            self.log_run_failed(
                run_owner=owner_name,
                run_project=project_name,
                run_uuid=run_uuid,
                exc=e,
                message="Agent failed during compilation with unknown exception.\n",
            )
        return None

    def submit_run(self, run_data: Tuple[str, str, str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        resource = self.prepare_run_resource(
            owner_name=run_owner,
            project_name=run_project,
            run_name=run_data[2],
            run_uuid=run_uuid,
            content=run_data[3],
        )
        if not resource:
            return

        try:
            self.executor.create(
                run_uuid=run_uuid, run_kind=run_data[1], resource=resource
            )
        except ApiException as e:
            if e.status == 409:
                logger.info("Run already running, triggering an apply mechanism.")
                self.apply_run(run_data=run_data)
            else:
                logger.info("Run submission error.")
                self.log_run_failed(
                    run_owner=run_owner,
                    run_project=run_project,
                    run_uuid=run_uuid,
                    exc=e,
                )
        except Exception as e:
            self.log_run_failed(
                run_owner=run_owner,
                run_project=run_project,
                run_uuid=run_uuid,
                exc=e,
            )

    def make_and_create_run(
        self, run_data: Tuple[str, str, str, str], default_auth: bool = False
    ):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        resource = self.make_run_resource(
            owner_name=run_owner,
            project_name=run_project,
            run_name=run_data[2],
            run_uuid=run_uuid,
            content=run_data[3],
            default_auth=default_auth,
        )
        if not resource:
            return

        try:
            self.executor.create(
                run_uuid=run_uuid, run_kind=run_data[1], resource=resource
            )
        except ApiException as e:
            if e.status == 409:
                logger.info("Run already running, triggering an apply mechanism.")
            else:
                logger.info("Run submission error.")
        except Exception as e:
            logger.info(
                "Run could not be cleaned. Agent failed converting run manifest: {}\n{}".format(
                    repr(e), traceback.format_exc()
                )
            )

    def apply_run(self, run_data: Tuple[str, str, str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        resource = self.prepare_run_resource(
            owner_name=run_owner,
            project_name=run_project,
            run_name=run_data[2],
            run_uuid=run_uuid,
            content=run_data[3],
        )
        if not resource:
            return

        try:
            self.executor.apply(
                run_uuid=run_uuid, run_kind=run_data[1], resource=resource
            )
            self.log_run_running(
                run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
            )
        except Exception as e:
            self.log_run_failed(
                run_owner=run_owner, run_project=run_project, run_uuid=run_uuid, exc=e
            )
            self.clean_run(run_uuid=run_uuid, run_kind=run_data[1])

    def check_run(self, run_data: Tuple[str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        try:
            self.executor.get(run_uuid=run_uuid, run_kind=run_data[1])
        except ApiException as e:
            if e.status == 404:
                logger.info(
                    "Run does not exist anymore, it could have been stopped or deleted."
                )
                self.log_run_stopped(
                    run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
                )

    def stop_run(self, run_data: Tuple[str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        try:
            self.executor.stop(run_uuid=run_uuid, run_kind=run_data[1])
        except ApiException as e:
            if e.status == 404:
                logger.info("Run does not exist anymore, it could have been stopped.")
                self.log_run_stopped(
                    run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
                )
        except Exception as e:
            self.log_run_failed(
                run_owner=run_owner,
                run_project=run_project,
                run_uuid=run_uuid,
                exc=e,
                message="Agent failed stopping run.\n",
            )

    def delete_run(self, run_data: Tuple[str, str, str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        self.clean_run(run_uuid=run_uuid, run_kind=run_data[1])
        if run_data[3]:
            self.make_and_create_run(run_data)