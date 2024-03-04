from typing import Dict, List, Optional

from clipped.compact.pydantic import Field
from clipped.utils.lists import to_list

from polyaxon import settings
from polyaxon._auxiliaries import (
    V1PolyaxonInitContainer,
    V1PolyaxonSidecarContainer,
    get_default_init_container,
    get_default_sidecar_container,
)
from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1CompiledOperation, V1Init
from polyaxon._schemas.agent import AgentConfig
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon.exceptions import PolyaxonCompilerError


class AgentResolver(BaseSchemaModel):
    polyaxon_sidecar: Optional[V1PolyaxonSidecarContainer]
    polyaxon_init: Optional[V1PolyaxonInitContainer]
    namespace: Optional[str]
    secrets: Optional[List[V1ConnectionResource]]
    config_maps: Optional[List[V1ConnectionResource]]
    connection_by_names: Optional[Dict[str, V1Connection]]
    artifacts_store: Optional[V1Connection]
    default_sa: Optional[str]
    internal_auth: Optional[bool] = Field(default=False)

    def resolve(
        self, compiled_operation: V1CompiledOperation, agent_config: AgentConfig = None
    ):
        if not agent_config and settings.AGENT_CONFIG:
            agent_config = settings.AGENT_CONFIG.clone()
        if not agent_config:
            raise PolyaxonCompilerError(
                "Agent configuration not found or agent not configured."
            )

        self.default_sa = agent_config.runs_sa
        self._resolve_run_connections(
            compiled_operation=compiled_operation, agent_config=agent_config
        )
        self.artifacts_store = agent_config.artifacts_store

        self.secrets = agent_config.secrets
        self.config_maps = agent_config.config_maps

        self.polyaxon_sidecar = agent_config.sidecar or get_default_sidecar_container()
        self.polyaxon_init = agent_config.init or get_default_init_container()
        if compiled_operation.namespace:
            namespaces = agent_config.additional_namespaces or []
            namespaces.append(agent_config.namespace)
            if compiled_operation.namespace not in namespaces:
                raise PolyaxonCompilerError(
                    "The provided namespace `{}` is not managed by the agent.".format(
                        compiled_operation.namespace
                    )
                )
            self.namespace = compiled_operation.namespace
        else:
            self.namespace = agent_config.namespace

    def _resolve_run_connections(
        self, compiled_operation: V1CompiledOperation, agent_config: AgentConfig
    ):
        if not self.connection_by_names:
            self.connection_by_names = {}
        if agent_config.artifacts_store:  # Resolve default artifacts store
            self.connection_by_names[
                agent_config.artifacts_store.name
            ] = agent_config.artifacts_store

        if (
            compiled_operation.is_job_run
            or compiled_operation.is_service_run
            or compiled_operation.is_notifier_run
            or compiled_operation.is_tuner_run
        ):
            self._resolve_replica_connections(
                init=compiled_operation.run.init,
                connections=compiled_operation.run.connections,
                agent_config=agent_config,
            )
        if compiled_operation.is_distributed_run:
            self._resolve_distributed_connections(
                compiled_operation=compiled_operation, agent_config=agent_config
            )
        if compiled_operation.is_dag_run:
            self._resolve_connections(
                connections=compiled_operation.run.connections,
                agent_config=agent_config,
            )

    def _resolve_connections(self, connections: List[str], agent_config: AgentConfig):
        if connections:
            connection_by_names = self.connection_by_names or {}
            missing_connections = set()
            for c in connections:
                if c not in agent_config.connections_by_names:
                    missing_connections.add(c)
                else:
                    connection_by_names[c] = agent_config.connections_by_names[c]
            if missing_connections:
                raise PolyaxonCompilerError(
                    "Some connection refs were provided "
                    "but were not found in the "
                    "agent.connections catalog: `{}`".format(missing_connections)
                )
            self.connection_by_names = connection_by_names

    def _resolve_replica_connections(
        self, connections: List[str], init: List[V1Init], agent_config: AgentConfig
    ):
        connections = to_list(connections, check_none=True)
        self._resolve_connections(connections=connections, agent_config=agent_config)
        init = to_list(init, check_none=True)
        init = [i.connection for i in init if i.connection]
        self._resolve_connections(connections=init, agent_config=agent_config)

    def _resolve_distributed_connections(
        self, compiled_operation: V1CompiledOperation, agent_config: AgentConfig
    ):
        def _resolve_replica(replica):
            if not replica:
                return
            self._resolve_replica_connections(
                init=replica.init,
                connections=replica.connections,
                agent_config=agent_config,
            )

        if compiled_operation.is_mpi_job_run:
            _resolve_replica(compiled_operation.run.launcher)
            _resolve_replica(compiled_operation.run.worker)
        elif compiled_operation.is_tf_job_run:
            _resolve_replica(compiled_operation.run.chief)
            _resolve_replica(compiled_operation.run.worker)
            _resolve_replica(compiled_operation.run.ps)
            _resolve_replica(compiled_operation.run.evaluator)
        elif (
            compiled_operation.is_pytorch_job_run
            or compiled_operation.is_paddle_job_run
        ):
            _resolve_replica(compiled_operation.run.master)
            _resolve_replica(compiled_operation.run.worker)
        elif compiled_operation.is_mx_job_run:
            _resolve_replica(compiled_operation.run.scheduler)
            _resolve_replica(compiled_operation.run.worker)
            _resolve_replica(compiled_operation.run.server)
            _resolve_replica(compiled_operation.run.tuner)
            _resolve_replica(compiled_operation.run.tuner_tracker)
            _resolve_replica(compiled_operation.run.tuner_server)
        elif compiled_operation.is_xgb_job_run:
            _resolve_replica(compiled_operation.run.master)
            _resolve_replica(compiled_operation.run.worker)
