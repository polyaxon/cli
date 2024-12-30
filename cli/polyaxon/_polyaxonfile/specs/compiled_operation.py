import copy

from typing import Dict, List, Optional, Set, Type, Union

from polyaxon._flow import (
    ParamSpec,
    V1CompiledOperation,
    V1Dag,
    V1Hook,
    V1Init,
    V1Param,
    validate_run_patch,
)
from polyaxon._polyaxonfile.specs import kinds
from polyaxon._polyaxonfile.specs.base import BaseSpecification
from polyaxon._polyaxonfile.specs.libs.parser import PolyaxonfileParser
from polyaxon._polyaxonfile.specs.operation import OperationSpecification
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


class CompiledOperationSpecification(BaseSpecification):
    """The polyaxonfile specification for compiled operation."""

    _SPEC_KIND = kinds.COMPILED_OPERATION

    CONFIG: Type[V1CompiledOperation] = V1CompiledOperation

    @staticmethod
    def dict_to_param_spec(
        contexts: Optional[Dict] = None,
        is_requested: bool = False,
        is_context: bool = False,
    ):
        contexts = contexts or {}
        return {
            k: ParamSpec(
                name=k,
                param=V1Param(value=v),
                type="Any",
                is_flag=False,
                is_list=None,
                is_requested=is_requested,
                is_context=is_context,
                arg_format=None,
            )
            for k, v in contexts.items()
        }

    @classmethod
    def calculate_context_spec(
        cls,
        config: V1CompiledOperation,
        contexts: Optional[Dict] = None,
        should_be_resolved: bool = False,
    ) -> Dict[str, ParamSpec]:
        param_spec = config.validate_params(
            is_template=False,
            check_all_refs=True,
            parse_values=True,
            parse_joins=not should_be_resolved,
        )
        if should_be_resolved:
            for p_spec in param_spec:
                if not p_spec.param.is_literal:
                    raise PolyaxonfileError(
                        "calculate_context_spec received a non-resolved "
                        "ref param `{}` with value `{}`".format(
                            p_spec.name, p_spec.param.to_dict()
                        )
                    )
        param_spec = {param.name: param for param in param_spec}
        param_spec.update(cls.dict_to_param_spec(contexts=contexts, is_context=True))
        return param_spec

    @classmethod
    def _apply_operation_contexts(
        cls,
        config: V1CompiledOperation,
        param_spec: Dict[str, ParamSpec] = None,
        contexts: Optional[Dict] = None,
    ) -> V1CompiledOperation:
        if not param_spec:
            param_spec = cls.calculate_context_spec(config=config, contexts=contexts)

        parsed_data = PolyaxonfileParser.parse_operation(config, param_spec or {})
        return cls.CONFIG.read(parsed_data)

    @staticmethod
    def _apply_dag_context(config: V1CompiledOperation) -> V1CompiledOperation:
        dag_run = config.run  # type: V1Dag
        dag_run.process_dag()
        dag_run.validate_dag()
        dag_run.process_components(config.inputs)
        return config

    @classmethod
    def apply_operation_contexts(
        cls,
        config: V1CompiledOperation,
        param_spec: Dict[str, ParamSpec] = None,
        contexts: Optional[Dict] = None,
    ) -> V1CompiledOperation:
        if config.is_dag_run:
            return cls._apply_dag_context(config)
        else:
            return cls._apply_operation_contexts(
                config=config, param_spec=param_spec, contexts=contexts
            )

    @classmethod
    def _apply_connections_params(
        cls,
        connections: List[str],
        init: List[V1Init],
        artifact_store: Optional[str] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ):
        if connections:
            connections = PolyaxonfileParser.parse_section(
                connections, param_spec=param_spec, parse_params=True
            )
        _init = []
        if init:
            for i in init:
                if (i.artifacts or i.paths) and not i.connection:
                    i.connection = artifact_store
                if i.connection:
                    i.connection = PolyaxonfileParser.parse_section(
                        i.connection, param_spec=param_spec, parse_params=True
                    )
                # resolved_i = V1Init.from_dict(
                #     PolyaxonfileParser.parse_section(
                #         i.to_dict(), param_spec=param_spec, parse_params=True
                #     )
                # )
                _init.append(i)

        # Prepend any param that has to_init after validation
        init_params = [v.to_init() for v in param_spec.values() if v.validate_to_init()]
        init_params = [v for v in init_params if v]
        _init = init_params + _init
        return _init, connections

    @classmethod
    def _apply_distributed_run_connections_params(
        cls,
        config: V1CompiledOperation,
        artifact_store: Optional[str] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ):
        def _resolve_replica(replica):
            if not replica:
                return
            init, connections = cls._apply_connections_params(
                init=replica.init,
                connections=replica.connections,
                artifact_store=artifact_store,
                param_spec=param_spec,
            )
            replica.init = init
            replica.connections = connections
            return replica

        if config.is_mpi_job_run:
            config.run.launcher = _resolve_replica(config.run.launcher)
            config.run.worker = _resolve_replica(config.run.worker)
        elif config.is_tf_job_run:
            config.run.chief = _resolve_replica(config.run.chief)
            config.run.worker = _resolve_replica(config.run.worker)
            config.run.ps = _resolve_replica(config.run.ps)
            config.run.evaluator = _resolve_replica(config.run.evaluator)
        elif config.is_pytorch_job_run or config.is_paddle_job_run:
            config.run.master = _resolve_replica(config.run.master)
            config.run.worker = _resolve_replica(config.run.worker)
        elif config.is_mx_job_run:
            config.run.scheduler = _resolve_replica(config.run.scheduler)
            config.run.worker = _resolve_replica(config.run.worker)
            config.run.server = _resolve_replica(config.run.server)
            config.run.tuner = _resolve_replica(config.run.tuner)
            config.run.tuner_tracker = _resolve_replica(config.run.tuner_tracker)
            config.run.tuner_server = _resolve_replica(config.run.tuner_server)
        elif config.is_xgb_job_run:
            config.run.master = _resolve_replica(config.run.master)
            config.run.worker = _resolve_replica(config.run.worker)
        return config

    @classmethod
    def apply_run_connections_params(
        cls,
        config: V1CompiledOperation,
        artifact_store: Optional[str] = None,
        contexts: Optional[Dict] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ) -> V1CompiledOperation:
        if not param_spec:
            param_spec = cls.calculate_context_spec(config=config, contexts=contexts)
        if config.is_job_run or config.is_service_run:
            init, connections = cls._apply_connections_params(
                init=config.run.init,
                connections=config.run.connections,
                artifact_store=artifact_store,
                param_spec=param_spec,
            )
            config.run.init = init
            config.run.connections = connections
            return config
        if config.is_distributed_run:
            return cls._apply_distributed_run_connections_params(
                config=config,
                artifact_store=artifact_store,
                param_spec=param_spec,
            )
        return config

    @classmethod
    def apply_params(
        cls,
        config: V1CompiledOperation,
        params: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ) -> V1CompiledOperation:
        config.apply_params(params, context)
        return config

    @classmethod
    def apply_section_contexts(
        cls,
        config: V1CompiledOperation,
        section,
        contexts: Optional[Dict] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ):
        if not param_spec:
            param_spec = cls.calculate_context_spec(config=config, contexts=contexts)

        return PolyaxonfileParser.parse_section(section, param_spec)

    @classmethod
    def _apply_runtime_contexts(
        cls,
        config: V1CompiledOperation,
        contexts: Optional[Dict] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ) -> V1CompiledOperation:
        if not param_spec:
            param_spec = cls.calculate_context_spec(
                config=config, contexts=contexts, should_be_resolved=True
            )
        parsed_data = PolyaxonfileParser.parse_runtime(config.to_dict(), param_spec)
        return cls.CONFIG.read(parsed_data)

    @classmethod
    def _apply_distributed_runtime_contexts(
        cls,
        config: V1CompiledOperation,
        contexts: Optional[Dict] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ) -> V1CompiledOperation:
        if not param_spec:
            # Calculate the param_space once with empty contexts
            replica_param_spec = cls.calculate_context_spec(
                config=config, contexts=None, should_be_resolved=True
            )
            param_spec = {}
            for k in contexts:
                param_spec[k] = copy.copy(replica_param_spec)
                param_spec[k].update(
                    cls.dict_to_param_spec(
                        contexts=contexts[k], is_requested=True, is_context=True
                    )
                )
        parsed_data = PolyaxonfileParser.parse_distributed_runtime(
            config.to_dict(), param_spec
        )
        return cls.CONFIG.read(parsed_data)

    @classmethod
    def apply_runtime_contexts(
        cls,
        config: V1CompiledOperation,
        contexts: Optional[Dict] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ) -> V1CompiledOperation:
        if config.has_pipeline:
            raise PolyaxonSchemaError(
                "This method is not allowed on this specification."
            )
        if config.is_distributed_run:
            return cls._apply_distributed_runtime_contexts(
                config=config,
                contexts=contexts,
                param_spec=param_spec,
            )
        else:
            return cls._apply_runtime_contexts(
                config=config,
                contexts=contexts,
                param_spec=param_spec,
            )

    @classmethod
    def apply_hooks_contexts(
        cls,
        config: V1CompiledOperation,
        contexts: Optional[Dict] = None,
        param_spec: Dict[str, ParamSpec] = None,
    ) -> List[V1Hook]:
        if not param_spec:
            param_spec = cls.calculate_context_spec(
                config=config, contexts=contexts, should_be_resolved=True
            )
        hooks = PolyaxonfileParser.parse_hooks(config, param_spec)
        return [V1Hook.read(hook) for hook in hooks]

    @classmethod
    def apply_preset(
        cls, config: V1CompiledOperation, preset: Union[Dict, str] = None
    ) -> V1CompiledOperation:
        if not preset:
            return config
        preset = OperationSpecification.read(
            preset, is_preset=True
        )  # type: V1Operation
        if preset.run_patch:
            config.run = config.run.patch(
                validate_run_patch(preset.run_patch, config.run.kind),
                strategy=preset.patch_strategy,
            )
        patch_keys = {
            "name",
            "description",
            "tags",
            "is_approved",
            "presets",
            "queue",
            "namespace",
            "cache",
            "build",
            "hooks",
            "events",
            "plugins",
            "termination",
            "matrix",
            "joins",
            "schedule",
            "dependencies",
            "trigger",
            "conditions",
            "skip_on_upstream_skip",
        }
        patch_keys = patch_keys.intersection(preset.model_fields_set)
        patch_data = {k: getattr(preset, k) for k in patch_keys}
        patch_compiled = V1CompiledOperation.construct(**patch_data)
        return config.patch(patch_compiled, strategy=preset.patch_strategy)

    @classmethod
    def _get_distributed_init_connections(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_connection_names = set()

        def _get_resolve_connections(replica):
            if replica and replica.init:
                return init_connection_names | set(
                    [i.connection for i in replica.init if i.connection]
                )
            return init_connection_names

        if compiled_operation.is_mpi_job_run:
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.launcher
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_tf_job_run:
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.chief
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.worker
            )
            init_connection_names = _get_resolve_connections(compiled_operation.run.ps)
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.evaluator
            )
        elif (
            compiled_operation.is_pytorch_job_run
            or compiled_operation.is_paddle_job_run
        ):
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.master
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_mx_job_run:
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.scheduler
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.worker
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.server
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.tuner
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.tuner_tracker
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.tuner_server
            )
        elif compiled_operation.is_xgb_job_run:
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.master
            )
            init_connection_names = _get_resolve_connections(
                compiled_operation.run.worker
            )

        return init_connection_names

    @classmethod
    def _get_init_connections(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_connection_names = set()
        if compiled_operation and not compiled_operation.has_pipeline:
            if compiled_operation.run.init:
                init_connection_names |= set(
                    [i.connection for i in compiled_operation.run.init if i.connection]
                )
        return init_connection_names

    @classmethod
    def get_init_connections(
        cls,
        config: V1CompiledOperation,
    ) -> Set[str]:
        if config.is_distributed_run:
            return cls._get_distributed_init_connections(
                compiled_operation=config,
            )
        else:
            return cls._get_init_connections(
                compiled_operation=config,
            )

    @classmethod
    def _get_distributed_connections(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        connections_names = set()

        def _get_resolve_connections(replica):
            if replica and replica.connections:
                return connections_names | set(replica.connections)
            return connections_names

        if compiled_operation.is_mpi_job_run:
            connections_names = _get_resolve_connections(
                compiled_operation.run.launcher
            )
            connections_names = _get_resolve_connections(compiled_operation.run.worker)
        elif compiled_operation.is_tf_job_run:
            connections_names = _get_resolve_connections(compiled_operation.run.chief)
            connections_names = _get_resolve_connections(compiled_operation.run.worker)
            connections_names = _get_resolve_connections(compiled_operation.run.ps)
            connections_names = _get_resolve_connections(
                compiled_operation.run.evaluator
            )
        elif (
            compiled_operation.is_pytorch_job_run
            or compiled_operation.is_paddle_job_run
        ):
            connections_names = _get_resolve_connections(compiled_operation.run.master)
            connections_names = _get_resolve_connections(compiled_operation.run.worker)
        elif compiled_operation.is_mx_job_run:
            connections_names = _get_resolve_connections(
                compiled_operation.run.scheduler
            )
            connections_names = _get_resolve_connections(compiled_operation.run.worker)
            connections_names = _get_resolve_connections(compiled_operation.run.server)
            connections_names = _get_resolve_connections(compiled_operation.run.tuner)
            connections_names = _get_resolve_connections(
                compiled_operation.run.tuner_tracker
            )
            connections_names = _get_resolve_connections(
                compiled_operation.run.tuner_server
            )
        elif compiled_operation.is_xgb_job_run:
            connections_names = _get_resolve_connections(compiled_operation.run.master)
            connections_names = _get_resolve_connections(compiled_operation.run.worker)

        return connections_names

    @classmethod
    def _get_connections(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        connections_names = set()
        if compiled_operation and compiled_operation.run.connections:
            connections_names |= set(compiled_operation.run.connections)
        return connections_names

    @classmethod
    def get_connections(
        cls,
        config: V1CompiledOperation,
    ) -> Set[str]:
        if config.is_distributed_run:
            return cls._get_distributed_connections(
                compiled_operation=config,
            )
        else:
            return cls._get_connections(
                compiled_operation=config,
            )

    @classmethod
    def _get_distributed_init_lineage_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_model_version_names = set()

        def _get_resolve_models(replica):
            if replica and replica.init:
                return init_model_version_names | set(
                    [i.lineage_ref for i in replica.init if i.lineage_ref]
                )
            return init_model_version_names

        if compiled_operation.is_mpi_job_run:
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.launcher
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_tf_job_run:
            init_model_version_names = _get_resolve_models(compiled_operation.run.chief)
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
            init_model_version_names = _get_resolve_models(compiled_operation.run.ps)
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.evaluator
            )
        elif (
            compiled_operation.is_pytorch_job_run
            or compiled_operation.is_paddle_job_run
        ):
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.master
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_mx_job_run:
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.scheduler
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.server
            )
            init_model_version_names = _get_resolve_models(compiled_operation.run.tuner)
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.tuner_tracker
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.tuner_server
            )
        elif compiled_operation.is_xgb_job_run:
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.master
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )

        return init_model_version_names

    @classmethod
    def _get_init_lineage_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_model_version_names = set()
        if compiled_operation and not compiled_operation.has_pipeline:
            if compiled_operation.run.init:
                init_model_version_names |= set(
                    [
                        i.lineage_ref
                        for i in compiled_operation.run.init
                        if i.lineage_ref
                    ]
                )
        return init_model_version_names

    @classmethod
    def get_init_lineage_refs(
        cls,
        config: V1CompiledOperation,
    ) -> Set[str]:
        if config.is_distributed_run:
            return cls._get_distributed_init_lineage_refs(
                compiled_operation=config,
            )
        else:
            return cls._get_init_lineage_refs(
                compiled_operation=config,
            )

    @classmethod
    def _get_distributed_init_model_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_model_version_names = set()

        def _get_resolve_models(replica):
            if replica and replica.init:
                return init_model_version_names | set(
                    [i.model_ref for i in replica.init if i.model_ref]
                )
            return init_model_version_names

        if compiled_operation.is_mpi_job_run:
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.launcher
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_tf_job_run:
            init_model_version_names = _get_resolve_models(compiled_operation.run.chief)
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
            init_model_version_names = _get_resolve_models(compiled_operation.run.ps)
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.evaluator
            )
        elif (
            compiled_operation.is_pytorch_job_run
            or compiled_operation.is_paddle_job_run
        ):
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.master
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_mx_job_run:
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.scheduler
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.server
            )
            init_model_version_names = _get_resolve_models(compiled_operation.run.tuner)
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.tuner_tracker
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.tuner_server
            )
        elif compiled_operation.is_xgb_job_run:
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.master
            )
            init_model_version_names = _get_resolve_models(
                compiled_operation.run.worker
            )

        return init_model_version_names

    @classmethod
    def _get_init_model_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_model_version_names = set()
        if compiled_operation and not compiled_operation.has_pipeline:
            if compiled_operation.run.init:
                init_model_version_names |= set(
                    [i.model_ref for i in compiled_operation.run.init if i.model_ref]
                )
        return init_model_version_names

    @classmethod
    def get_init_model_refs(
        cls,
        config: V1CompiledOperation,
    ) -> Set[str]:
        if config.is_distributed_run:
            return cls._get_distributed_init_model_refs(
                compiled_operation=config,
            )
        else:
            return cls._get_init_model_refs(
                compiled_operation=config,
            )

    @classmethod
    def _get_distributed_init_artifact_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_artifact_version_names = set()

        def _get_resolve_artifacts(replica):
            if replica and replica.init:
                return init_artifact_version_names | set(
                    [i.artifact_ref for i in replica.init if i.artifact_ref]
                )
            return init_artifact_version_names

        if compiled_operation.is_mpi_job_run:
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.launcher
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_tf_job_run:
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.chief
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.worker
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.ps
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.evaluator
            )
        elif (
            compiled_operation.is_pytorch_job_run
            or compiled_operation.is_paddle_job_run
        ):
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.master
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_mx_job_run:
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.scheduler
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.worker
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.server
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.tuner
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.tuner_tracker
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.tuner_server
            )
        elif compiled_operation.is_xgb_job_run:
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.master
            )
            init_artifact_version_names = _get_resolve_artifacts(
                compiled_operation.run.worker
            )

        return init_artifact_version_names

    @classmethod
    def _get_init_artifact_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> Set[str]:
        init_artifact_version_names = set()
        if compiled_operation and not compiled_operation.has_pipeline:
            if compiled_operation.run.init:
                init_artifact_version_names |= set(
                    [
                        i.artifact_ref
                        for i in compiled_operation.run.init
                        if i.artifact_ref
                    ]
                )
        return init_artifact_version_names

    @classmethod
    def get_init_artifact_refs(
        cls,
        config: V1CompiledOperation,
    ) -> Set[str]:
        if config.is_distributed_run:
            return cls._get_distributed_init_artifact_refs(
                compiled_operation=config,
            )
        else:
            return cls._get_init_artifact_refs(
                compiled_operation=config,
            )

    @classmethod
    def _clean_distributed_init_version_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> V1CompiledOperation:
        def _clean_resolve_refs(replica):
            if replica and replica.init:
                replica.init = [
                    i
                    for i in replica.init
                    if (
                        i.model_ref is None
                        and i.artifact_ref is None
                        and i.lineage_ref is None
                    )
                ]
                return replica
            return replica

        if compiled_operation.is_mpi_job_run:
            compiled_operation.run.launcher = _clean_resolve_refs(
                compiled_operation.run.launcher
            )
            compiled_operation.run.worker = _clean_resolve_refs(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_tf_job_run:
            compiled_operation.run.chief = _clean_resolve_refs(
                compiled_operation.run.chief
            )
            compiled_operation.run.worker = _clean_resolve_refs(
                compiled_operation.run.worker
            )
            compiled_operation.run.ps = _clean_resolve_refs(compiled_operation.run.ps)
            compiled_operation.run.evaluator = _clean_resolve_refs(
                compiled_operation.run.evaluator
            )
        elif (
            compiled_operation.is_pytorch_job_run
            or compiled_operation.is_paddle_job_run
        ):
            compiled_operation.run.master = _clean_resolve_refs(
                compiled_operation.run.master
            )
            compiled_operation.run.worker = _clean_resolve_refs(
                compiled_operation.run.worker
            )
        elif compiled_operation.is_mx_job_run:
            compiled_operation.run.scheduler = _clean_resolve_refs(
                compiled_operation.run.scheduler
            )
            compiled_operation.run.worker = _clean_resolve_refs(
                compiled_operation.run.worker
            )
            compiled_operation.run.server = _clean_resolve_refs(
                compiled_operation.run.server
            )
            compiled_operation.run.tuner = _clean_resolve_refs(
                compiled_operation.run.tuner
            )
            compiled_operation.run.tuner_tracker = _clean_resolve_refs(
                compiled_operation.run.tuner_tracker
            )
            compiled_operation.run.tuner_server = _clean_resolve_refs(
                compiled_operation.run.tuner_server
            )
        elif compiled_operation.is_xgb_job_run:
            compiled_operation.run.master = _clean_resolve_refs(
                compiled_operation.run.master
            )
            compiled_operation.run.worker = _clean_resolve_refs(
                compiled_operation.run.worker
            )

        return compiled_operation

    @classmethod
    def _clean_init_version_refs(
        cls,
        compiled_operation: V1CompiledOperation,
    ) -> V1CompiledOperation:
        if compiled_operation and not compiled_operation.has_pipeline:
            if compiled_operation.run.init:
                compiled_operation.run.init = [
                    i
                    for i in compiled_operation.run.init
                    if (
                        i.model_ref is None
                        and i.artifact_ref is None
                        and i.lineage_ref is None
                    )
                ]
        return compiled_operation

    @classmethod
    def clean_init_version_refs(
        cls,
        config: V1CompiledOperation,
    ) -> V1CompiledOperation:
        if config.is_distributed_run:
            return cls._clean_distributed_init_version_refs(
                compiled_operation=config,
            )
        else:
            return cls._clean_init_version_refs(
                compiled_operation=config,
            )
