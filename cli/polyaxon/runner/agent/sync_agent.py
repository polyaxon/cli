import time
import traceback

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, Tuple

from clipped.utils.tz import now
from clipped.utils.versions import clean_version_for_check
from clipped.utils.workers import get_pool_workers, get_wait, sync_exit_context
from kubernetes.client.rest import ApiException
from urllib3.exceptions import HTTPError

from polyaxon import pkg, settings
from polyaxon.env_vars.getters import get_run_info
from polyaxon.exceptions import PolyaxonAgentError, PolyaxonConverterError
from polyaxon.logger import logger
from polyaxon.runner.agent.base_agent import BaseAgent
from polyaxon.schemas.responses.v1_agent import V1Agent
from polyaxon.schemas.responses.v1_agent_state_response import V1AgentStateResponse
from polyaxon.sdk.exceptions import ApiException as SDKApiException


class BaseSyncAgent(BaseAgent):
    IS_ASYNC = False

    def _enter(self):
        if not self.client._is_managed:
            return self
        print("Agent is starting.")
        try:
            agent = self.client.get_info()
            self._check_status(agent)
            self.sync()
            self.client.log_agent_running()
            print("Agent is running.")
            return self
        except (ApiException, SDKApiException, HTTPError) as e:
            message = "Could not start the agent."
            if e.status == 404:
                reason = "Agent not found."
            elif e.status == 403:
                reason = "Agent is not approved yet or has invalid token."
            else:
                reason = "Error {}.".format(repr(e))
            self.client.log_agent_failed(message="{} {}".format(message, reason))
            raise PolyaxonAgentError(message="{} {}".format(message, reason))

    def _exit(self):
        if not self.client._is_managed:
            return
        if not self._graceful_shutdown:
            self.client.log_agent_warning()
        time.sleep(1)

    def __enter__(self):
        return self._enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit()

    def refresh_executor(self):
        if (
            now() - self._executor_refreshed_at
        ).total_seconds() > settings.AGENT_CONFIG.get_executor_refresh_interval():
            logger.debug("Refreshing executor ... ")
            self.executor.refresh()
            self._executor_refreshed_at = now()

    def sync(self):
        return self.client.sync_agent(
            agent=V1Agent(
                content=settings.AGENT_CONFIG.to_json(),
                version=clean_version_for_check(pkg.VERSION),
                version_api=self.executor.manager.get_version(),
            ),
        )

    def start(self):
        try:
            with sync_exit_context() as exit_event:
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

    def process(self, pool: "ThreadPoolExecutor") -> V1AgentStateResponse:
        try:
            agent_state = self.client.get_state()
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

    def prepare_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
    ) -> Optional[Any]:
        try:
            return self.executor.convert(
                owner_name=owner_name,
                project_name=project_name,
                run_name=run_name,
                run_uuid=run_uuid,
                content=content,
                default_auth=True,
                agent_content=self.content,
            )
        except PolyaxonConverterError as e:
            self.client.log_run_failed(
                run_owner=owner_name,
                run_project=project_name,
                run_uuid=run_uuid,
                exc=e,
                message="Agent failed converting run manifest.\n",
            )
        except Exception as e:
            self.client.log_run_failed(
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
                self.client.log_run_failed(
                    run_owner=run_owner,
                    run_project=run_project,
                    run_uuid=run_uuid,
                    exc=e,
                )
        except Exception as e:
            self.client.log_run_failed(
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
            self.client.log_run_running(
                run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
            )
        except Exception as e:
            self.client.log_run_failed(
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
                self.client.log_run_stopped(
                    run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
                )

    def stop_run(self, run_data: Tuple[str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        try:
            self.executor.stop(run_uuid=run_uuid, run_kind=run_data[1])
        except ApiException as e:
            if e.status == 404:
                logger.info("Run does not exist anymore, it could have been stopped.")
                self.client.log_run_stopped(
                    run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
                )
        except Exception as e:
            self.client.log_run_failed(
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