import asyncio
import traceback

from typing import Any, Optional, Tuple

from clipped.utils.tz import now
from clipped.utils.versions import clean_version_for_check
from clipped.utils.workers import async_exit_context, get_wait
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


class BaseAsyncAgent(BaseAgent):
    IS_ASYNC = True

    async def _enter(self):
        if not self.client._is_managed:
            return self
        print("Agent is starting.")
        await self.executor.refresh()
        try:
            agent = await self.client.get_info()
            self._check_status(agent)
            await self.sync()
            await self.client.log_agent_running()
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
            await self.client.log_agent_failed(message="{} {}".format(message, reason))
            raise PolyaxonAgentError(message="{} {}".format(message, reason))

    async def _exit(self):
        if not self.client._is_managed:
            return
        if not self._graceful_shutdown:
            await self.client.log_agent_warning()
        await asyncio.sleep(1)

    async def __aenter__(self):
        return await self._enter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit()

    async def refresh_executor(self):
        if (
            now() - self._executor_refreshed_at
        ).total_seconds() > settings.AGENT_CONFIG.get_executor_refresh_interval():
            logger.debug("Refreshing executor ... ")
            await self.executor.refresh()
            self._executor_refreshed_at = now()

    async def sync(self):
        version_api = await self.executor.manager.get_version()
        return await self.client.sync_agent(
            agent=V1Agent(
                content=settings.AGENT_CONFIG.to_json(),
                version=clean_version_for_check(pkg.VERSION),
                version_api=version_api,
            ),
        )

    async def start(self):
        try:
            async with async_exit_context() as exit_event:
                index = 0
                timeout = self.sleep_interval or get_wait(index)

                while True:
                    try:
                        await asyncio.wait_for(exit_event.wait(), timeout=timeout)
                        break  # If exit_event is set, we break out of the loop
                    except asyncio.TimeoutError:
                        index += 1
                        await self.refresh_executor()
                        print("Refreshing agent ...")
                        agent_state = await self.process()
                        print("Agent state: {}".format(agent_state))
                        self._check_status(agent_state)
                        if agent_state.state.full:
                            index = 2
                        self.ping()
                        timeout = self.sleep_interval or get_wait(index)
                        logger.info("Sleeping for {} seconds".format(timeout))
        except Exception as e:
            print(e)
        finally:
            self.end()

    async def process(self, **kwargs) -> V1AgentStateResponse:
        try:
            agent_state = await self.client.get_state()
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
                await self.submit_run(run_data)
            for run_data in state.queued or []:
                await self.submit_run(run_data)
            for run_data in state.checks or []:
                await self.check_run(run_data)
            for run_data in state.stopping or []:
                await self.stop_run(run_data)
            for run_data in state.apply or []:
                await self.apply_run(run_data)
            for run_data in state.deleting or []:
                await self.delete_run(run_data)
            for run_data in state.hooks or []:
                await self.make_and_create_run(run_data)
            for run_data in state.watchdogs or []:
                await self.make_and_create_run(run_data)
            for run_data in state.tuners or []:
                await self.make_and_create_run(run_data, True)
            return agent_state
        except Exception as exc:
            logger.error(exc)
            return V1AgentStateResponse.construct()

    async def prepare_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
    ) -> Optional[Any]:
        try:
            return await self.executor.convert(
                owner_name=owner_name,
                project_name=project_name,
                run_name=run_name,
                run_uuid=run_uuid,
                content=content,
                default_auth=True,
                agent_content=self.content,
            )
        except PolyaxonConverterError as e:
            await self.client.log_run_failed(
                run_owner=owner_name,
                run_project=project_name,
                run_uuid=run_uuid,
                exc=e,
                message="Agent failed converting run manifest.\n",
            )
        except Exception as e:
            await self.client.log_run_failed(
                run_owner=owner_name,
                run_project=project_name,
                run_uuid=run_uuid,
                exc=e,
                message="Agent failed during compilation with unknown exception.\n",
            )
        return None

    async def submit_run(self, run_data: Tuple[str, str, str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        resource = await self.prepare_run_resource(
            owner_name=run_owner,
            project_name=run_project,
            run_name=run_data[2],
            run_uuid=run_uuid,
            content=run_data[3],
        )
        if not resource:
            return

        try:
            await self.executor.create(
                run_uuid=run_uuid, run_kind=run_data[1], resource=resource
            )
        except ApiException as e:
            if e.status == 409:
                logger.info("Run already running, triggering an apply mechanism.")
                await self.apply_run(run_data=run_data)
            else:
                logger.info("Run submission error.")
                await self.client.log_run_failed(
                    run_owner=run_owner,
                    run_project=run_project,
                    run_uuid=run_uuid,
                    exc=e,
                )
        except Exception as e:
            await self.client.log_run_failed(
                run_owner=run_owner,
                run_project=run_project,
                run_uuid=run_uuid,
                exc=e,
            )

    async def make_and_create_run(
        self, run_data: Tuple[str, str, str, str], default_auth: bool = False
    ):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        resource = await self.make_run_resource(
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
            await self.executor.create(
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

    async def apply_run(self, run_data: Tuple[str, str, str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        resource = await self.prepare_run_resource(
            owner_name=run_owner,
            project_name=run_project,
            run_name=run_data[2],
            run_uuid=run_uuid,
            content=run_data[3],
        )
        if not resource:
            return

        try:
            await self.executor.apply(
                run_uuid=run_uuid, run_kind=run_data[1], resource=resource
            )
            await self.client.log_run_running(
                run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
            )
        except Exception as e:
            await self.client.log_run_failed(
                run_owner=run_owner, run_project=run_project, run_uuid=run_uuid, exc=e
            )
            await self.clean_run(run_uuid=run_uuid, run_kind=run_data[1])

    async def check_run(self, run_data: Tuple[str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        try:
            await self.executor.get(run_uuid=run_uuid, run_kind=run_data[1])
        except ApiException as e:
            if e.status == 404:
                logger.info(
                    "Run does not exist anymore, it could have been stopped or deleted."
                )
                await self.client.log_run_stopped(
                    run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
                )

    async def stop_run(self, run_data: Tuple[str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        try:
            await self.executor.stop(run_uuid=run_uuid, run_kind=run_data[1])
        except ApiException as e:
            if e.status == 404:
                logger.info("Run does not exist anymore, it could have been stopped.")
                await self.client.log_run_stopped(
                    run_owner=run_owner, run_project=run_project, run_uuid=run_uuid
                )
        except Exception as e:
            await self.client.log_run_failed(
                run_owner=run_owner,
                run_project=run_project,
                run_uuid=run_uuid,
                exc=e,
                message="Agent failed stopping run.\n",
            )

    async def delete_run(self, run_data: Tuple[str, str, str, str]):
        run_owner, run_project, run_uuid = get_run_info(run_instance=run_data[0])
        await self.clean_run(run_uuid=run_uuid, run_kind=run_data[1])
        if run_data[3]:
            await self.make_and_create_run(run_data)

    async def clean_run(self, run_uuid: str, run_kind: str):
        try:
            await self.executor.clean(run_uuid=run_uuid, run_kind=run_kind)
            await self.executor.stop(run_uuid=run_uuid, run_kind=run_kind)
        except ApiException as e:
            if e.status == 404:
                logger.info("Run does not exist.")
        except Exception as e:
            logger.info(
                "Run could not be cleaned: {}\n{}".format(
                    repr(e), traceback.format_exc()
                )
            )