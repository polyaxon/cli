import time
import traceback

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, Optional, Tuple

from clipped.utils.tz import now
from clipped.utils.workers import exit_context, get_pool_workers, get_wait
from kubernetes.client.rest import ApiException

from polyaxon import live_state, settings
from polyaxon.auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon.client import PolyaxonClient
from polyaxon.compiler import resolver
from polyaxon.compiler.resolver import AgentResolver
from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.env_vars.getters import get_run_info
from polyaxon.exceptions import PolyaxonCompilerError, PolyaxonConverterError
from polyaxon.lifecycle import V1StatusCondition, V1Statuses
from polyaxon.logger import logger
from polyaxon.polyaxonfile import CompiledOperationSpecification, OperationSpecification
from polyaxon.polyflow import V1CompiledOperation
from polyaxon.runner.kinds import RunnerKind
from polyaxon.schemas.cli.agent_config import AgentConfig
from polyaxon.schemas.cli.checks_config import ChecksConfig
from polyaxon.schemas.responses.v1_agent import V1Agent
from polyaxon.schemas.responses.v1_agent_state_response import V1AgentStateResponse


class BaseAgent:
    RUNNER_KIND: RunnerKind
    CONVERTERS: Dict[str, Any]
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
        default_sa: Optional[str] = None,
        internal_auth: bool = False,
        default_auth: bool = False,
    ) -> Optional[Any]:
        operation = OperationSpecification.read(content)
        compiled_operation = OperationSpecification.compile_operation(operation)
        resolver_obj, compiled_operation = resolver.resolve(
            compiled_operation=compiled_operation,
            owner_name=owner_name,
            project_name=project_name,
            project_uuid=project_name,
            run_name=run_name,
            run_path=run_uuid,
            run_uuid=run_uuid,
            params=operation.params,
        )
        return self._get_resource(
            namespace=resolver_obj.namespace,
            owner_name=resolver_obj.owner_name,
            project_name=resolver_obj.project_name,
            run_name=resolver_obj.run_name,
            run_path=resolver_obj.run_path,
            run_uuid=resolver_obj.run_uuid,
            compiled_operation=compiled_operation,
            connection_by_names=resolver_obj.connection_by_names,
            internal_auth=internal_auth,
            artifacts_store=resolver_obj.artifacts_store,
            secrets=resolver_obj.secrets,
            config_maps=resolver_obj.config_maps,
            polyaxon_sidecar=resolver_obj.polyaxon_sidecar,
            polyaxon_init=resolver_obj.polyaxon_init,
            default_sa=default_sa,
            default_auth=default_auth,
        )

    def make_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
        default_auth=False,
    ) -> Optional[Any]:
        try:
            return self._make_and_convert(
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

    def _get_resource(
        self,
        namespace: Optional[str],
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        run_path: str,
        compiled_operation: V1CompiledOperation,
        artifacts_store: Optional[V1Connection],
        connection_by_names: Optional[Dict[str, V1Connection]],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        polyaxon_sidecar: Optional[V1PolyaxonSidecarContainer] = None,
        polyaxon_init: Optional[V1PolyaxonInitContainer] = None,
        default_sa: Optional[str] = None,
        internal_auth: bool = False,
        default_auth: bool = False,
    ):
        if not namespace and self.RUNNER_KIND == RunnerKind.K8S:
            raise PolyaxonCompilerError(
                "Converter Error. "
                "Namespace is required to create a k8s resource specification."
            )
        if compiled_operation.has_pipeline:
            raise PolyaxonCompilerError(
                "Converter Error. "
                "Specification with matrix/dag/schedule section is not supported in this function."
            )

        run_kind = compiled_operation.get_run_kind()
        if run_kind not in self.CONVERTERS:
            raise PolyaxonCompilerError(
                "Converter Error. "
                "Specification with run kind: {} is not supported in this deployment version.".format(
                    run_kind
                )
            )

        converter = self.CONVERTERS[run_kind](
            owner_name=owner_name,
            project_name=project_name,
            run_name=run_name,
            run_uuid=run_uuid,
            namespace=namespace,
            polyaxon_init=polyaxon_init,
            polyaxon_sidecar=polyaxon_sidecar,
            internal_auth=internal_auth,
            run_path=run_path,
        )
        if converter:
            return converter.get_resource(
                compiled_operation=compiled_operation,
                artifacts_store=artifacts_store,
                connection_by_names=connection_by_names,
                secrets=secrets,
                config_maps=config_maps,
                default_sa=default_sa,
                default_auth=default_auth,
            )

    def _convert(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
        default_auth: bool,
        agent_content: Optional[str] = None,
    ) -> Optional[Any]:
        agent_env = AgentResolver.construct()
        compiled_operation = CompiledOperationSpecification.read(content)

        agent_env.resolve(
            compiled_operation=compiled_operation,
            agent_config=AgentConfig.read(agent_content) if agent_content else None,
        )
        return self._get_resource(
            owner_name=owner_name,
            project_name=project_name,
            run_name=run_name,
            run_uuid=run_uuid,
            run_path=run_uuid,
            namespace=agent_env.namespace,
            compiled_operation=compiled_operation,
            polyaxon_init=agent_env.polyaxon_init,
            polyaxon_sidecar=agent_env.polyaxon_sidecar,
            artifacts_store=agent_env.artifacts_store,
            connection_by_names=agent_env.connection_by_names,
            secrets=agent_env.secrets,
            config_maps=agent_env.config_maps,
            default_sa=agent_env.default_sa,
        )

    def prepare_run_resource(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
    ) -> Optional[Any]:
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
        except PolyaxonConverterError as e:
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
