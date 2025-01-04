from datetime import datetime
from typing import Dict, List, Optional

from polyaxon import settings
from polyaxon._compiler.contexts import resolve_contexts, resolve_globals_contexts
from polyaxon._compiler.lineage import resolve_artifacts_lineage
from polyaxon._compiler.resolver import AgentResolver
from polyaxon._flow import V1CloningKind, V1CompiledOperation, V1Operation, V1RunKind
from polyaxon._polyaxonfile import CompiledOperationSpecification
from polyaxon.exceptions import PolyaxonCompilerError


class BaseResolver:
    KINDS = {
        V1RunKind.JOB,
        V1RunKind.SERVICE,
        V1RunKind.MPIJOB,
        V1RunKind.TFJOB,
        V1RunKind.PADDLEJOB,
        V1RunKind.PYTORCHJOB,
        V1RunKind.MXJOB,
        V1RunKind.XGBJOB,
        V1RunKind.NOTIFIER,
        V1RunKind.CLEANER,
        V1RunKind.TUNER,
        V1RunKind.WATCHDOG,
        V1RunKind.DAG,
        V1RunKind.DASKJOB,
        V1RunKind.RAYJOB,
        V1RunKind.TUNER,
    }

    def __init__(
        self,
        run,
        compiled_operation: V1CompiledOperation,
        owner_name: str,
        project_name: str,
        project_uuid: str,
        run_name: str,
        run_uuid: str,
        run_path: str,
        params: Optional[Dict],
        created_at: Optional[datetime] = None,
        compiled_at: Optional[datetime] = None,
        cloning_kind: V1CloningKind = None,
        original_uuid: Optional[str] = None,
        is_independent: bool = True,
        username: Optional[str] = None,
    ):
        if not compiled_operation:
            raise PolyaxonCompilerError("A run spec is required for resolution.")
        self.run = run
        self.compiled_operation = compiled_operation
        self.owner_name = owner_name
        self.username = username
        self.project_name = project_name
        self.project_uuid = project_uuid
        self.project_uuid = project_uuid or project_name
        self.run_name = run_name
        self.run_uuid = run_uuid or run_name
        self.run_path = run_path
        self.params = params or {}
        self.connection_by_names = {}
        self.namespace = None
        self.artifacts_store = None
        self.secrets = None
        self.config_maps = None
        self.polyaxon_sidecar = None
        self.polyaxon_init = None
        self.iteration = None
        self.agent_config = None
        self.globals = {}
        self.artifacts = []
        self.created_at = created_at
        self.compiled_at = compiled_at
        self.schedule_at = None
        self.started_at = None
        self.finished_at = None
        self.duration = None
        self.cloning_kind = cloning_kind
        self.original_uuid = original_uuid
        self.is_independent = is_independent
        self._param_spec = {}

    @classmethod
    def is_valid(cls, compiled_operation: V1CompiledOperation):
        compiled_operation.validate_build()
        run_kind = compiled_operation.get_run_kind()
        if run_kind not in cls.KINDS:
            raise PolyaxonCompilerError(
                "Resolver Error. "
                "Specification with run kind: {} "
                "is not supported in this deployment version.".format(run_kind)
            )

    @property
    def param_spec(self):
        return self._param_spec

    def resolve_edges(self):
        pass

    def resolve_globals_contexts(self):
        self.globals = resolve_globals_contexts(
            namespace=self.namespace,
            owner_name=self.owner_name,
            project_name=self.project_name,
            project_uuid=self.project_uuid,
            username=self.username,
            run_uuid=self.run_uuid,
            run_name=self.run_name,
            run_path=self.run_path,
            iteration=self.iteration,
            created_at=self.created_at,
            compiled_at=self.compiled_at,
            schedule_at=self.schedule_at,
            started_at=self.started_at,
            finished_at=self.finished_at,
            duration=self.duration,
            cloning_kind=self.cloning_kind,
            original_uuid=self.original_uuid,
            is_independent=self.is_independent,
        )

    def resolve_params(self):
        pass

    def apply_params(self, should_be_resolved: bool = True):
        self.compiled_operation = CompiledOperationSpecification.apply_params(
            config=self.compiled_operation,
            params=self.params,
            context=self.globals,
        )
        self._param_spec = CompiledOperationSpecification.calculate_context_spec(
            config=self.compiled_operation,
            contexts=self.globals,
            should_be_resolved=should_be_resolved,
        )

    def resolve_connections_params(self):
        self.compiled_operation = (
            CompiledOperationSpecification.apply_run_connections_params(
                config=self.compiled_operation,
                artifact_store=self.agent_config.artifacts_store.name
                if self.agent_config
                else None,
                contexts=self.globals,
                param_spec=self.param_spec,
            )
        )

    def resolve_presets(self):
        pass

    def resolve_agent(self):
        if settings.AGENT_CONFIG:
            self.agent_config = settings.AGENT_CONFIG.clone()

    def apply_operation_contexts(self):
        try:
            self.compiled_operation = (
                CompiledOperationSpecification.apply_operation_contexts(
                    self.compiled_operation,
                    param_spec=self.param_spec,
                    contexts=self.globals,
                )
            )
        except Exception as e:
            raise PolyaxonCompilerError(
                "Could not apply run context, error: {}".format(repr(e))
            )

    def resolve_io(self):
        pass

    def resolve_access(self):
        pass

    def resolve_agent_environment(self):
        agent_env = AgentResolver.construct()
        agent_env.resolve(
            compiled_operation=self.compiled_operation, agent_config=self.agent_config
        )
        self.polyaxon_sidecar = agent_env.polyaxon_sidecar
        self.polyaxon_init = agent_env.polyaxon_init
        self.namespace = agent_env.namespace
        self.secrets = agent_env.secrets
        self.config_maps = agent_env.config_maps
        self.connection_by_names = agent_env.connection_by_names
        self.artifacts_store = agent_env.artifacts_store

    def resolve_init_refs(self):
        pass

    def clean_init_refs(self):
        pass

    def resolve_actions(self):
        pass

    def resolve_artifacts_lineage(self):
        self.artifacts += resolve_artifacts_lineage(
            owner_name=self.owner_name,
            project_name=self.project_name,
            project_uuid=self.project_uuid,
            run_name=self.run_name,
            run_path=self.run_path,
            run_uuid=self.run_uuid,
            param_spec=self.param_spec,
            compiled_operation=self.compiled_operation,
            connection_by_names=self.connection_by_names,
            artifacts_store=self.artifacts_store,
        )

    def _resolve_contexts(self):
        return resolve_contexts(
            namespace=self.namespace,
            owner_name=self.owner_name,
            project_name=self.project_name,
            project_uuid=self.project_uuid,
            run_uuid=self.run_uuid,
            run_name=self.run_name,
            run_path=self.run_path,
            compiled_operation=self.compiled_operation,
            artifacts_store=self.artifacts_store,
            connection_by_names=self.connection_by_names,
            iteration=self.iteration,
            created_at=self.created_at,
            compiled_at=self.compiled_at,
            schedule_at=self.schedule_at,
            started_at=self.started_at,
            finished_at=self.finished_at,
            duration=self.duration,
            cloning_kind=self.cloning_kind,
            original_uuid=self.original_uuid,
            is_independent=self.is_independent,
            username=self.username,
        )

    def _apply_runtime_contexts(self):
        contexts = self._resolve_contexts()
        return CompiledOperationSpecification.apply_runtime_contexts(
            self.compiled_operation, contexts=contexts
        )

    def _apply_pipeline_contexts(self):
        return self.compiled_operation

    def _should_skip_runtime_resolution(self):
        return False

    def apply_runtime_contexts(self):
        if self._should_skip_runtime_resolution():
            return
        if self.compiled_operation.has_pipeline:
            self.compiled_operation = self._apply_pipeline_contexts()
        else:
            self.compiled_operation = self._apply_runtime_contexts()

    def resolve_state(self):
        pass

    def persist_state(self):
        pass

    def resolve_build(self):
        raise PolyaxonCompilerError(
            "Build resolution is not supported in this Polyaxon distribution"
        )

    def resolve_hooks(self) -> List[V1Operation]:
        raise PolyaxonCompilerError(
            "Hooks resolution is not supported in this Polyaxon distribution"
        )

    def resolve(self) -> V1CompiledOperation:
        self.resolve_edges()
        self.resolve_globals_contexts()
        self.resolve_params()
        self.apply_params()
        self.resolve_presets()
        self.resolve_agent()
        self.resolve_connections_params()
        self.apply_operation_contexts()
        self.resolve_io()
        self.resolve_init_refs()
        self.resolve_agent_environment()
        self.resolve_access()
        self.resolve_artifacts_lineage()
        self.clean_init_refs()
        self.resolve_state()
        self.apply_runtime_contexts()
        self.persist_state()
        return self.compiled_operation
