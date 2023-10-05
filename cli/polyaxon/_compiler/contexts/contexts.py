import os

from datetime import datetime
from typing import Dict, Optional

from polyaxon._compiler.contexts.dask_job import DaskJobContextsManager
from polyaxon._compiler.contexts.job import JobContextsManager
from polyaxon._compiler.contexts.kubeflow import (
    MPIJobContextsManager,
    MXJobContextsManager,
    PaddleJobContextsManager,
    PytorchJobContextsManager,
    TfJobContextsManager,
    XGBoostJobContextsManager,
)
from polyaxon._compiler.contexts.ray_job import RayJobContextsManager
from polyaxon._compiler.contexts.service import ServiceContextsManager
from polyaxon._connections import V1Connection
from polyaxon._contexts import keys as ctx_keys
from polyaxon._contexts import paths as ctx_paths
from polyaxon._contexts import sections as ctx_sections
from polyaxon._flow import V1CloningKind, V1CompiledOperation, V1Plugins, V1RunKind
from polyaxon._utils.fqn_utils import get_project_instance, get_run_instance
from polyaxon.exceptions import PolyaxonCompilerError

CONTEXTS_MANAGERS = {
    V1RunKind.CLEANER: JobContextsManager,
    V1RunKind.NOTIFIER: JobContextsManager,
    V1RunKind.TUNER: JobContextsManager,
    V1RunKind.WATCHDOG: JobContextsManager,
    V1RunKind.JOB: JobContextsManager,
    V1RunKind.SERVICE: ServiceContextsManager,
    V1RunKind.MPIJOB: MPIJobContextsManager,
    V1RunKind.TFJOB: TfJobContextsManager,
    V1RunKind.MXJOB: MXJobContextsManager,
    V1RunKind.XGBJOB: XGBoostJobContextsManager,
    V1RunKind.PYTORCHJOB: PytorchJobContextsManager,
    V1RunKind.PADDLEJOB: PaddleJobContextsManager,
    V1RunKind.RAYJOB: RayJobContextsManager,
    V1RunKind.DASKJOB: DaskJobContextsManager,
}


def resolve_globals_contexts(
    namespace: str,
    owner_name: str,
    project_name: str,
    project_uuid: str,
    run_uuid: str,
    run_name: str,
    run_path: str,
    iteration: int,
    created_at: datetime,
    compiled_at: datetime,
    schedule_at: Optional[datetime] = None,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    duration: Optional[float] = None,
    plugins: Optional[V1Plugins] = None,
    artifacts_store: V1Connection = None,
    cloning_kind: V1CloningKind = None,
    original_uuid: Optional[str] = None,
    is_independent: bool = True,
) -> Dict:
    resolved_contexts = {
        ctx_sections.GLOBALS: {
            ctx_keys.OWNER_NAME: owner_name,
            ctx_keys.PROJECT_NAME: project_name,
            ctx_keys.PROJECT_UNIQUE_NAME: get_project_instance(
                owner_name, project_name
            ),
            ctx_keys.PROJECT_UUID: project_uuid,
            ctx_keys.RUN_INFO: get_run_instance(owner_name, project_name, run_uuid),
            ctx_keys.NAME: run_name,
            ctx_keys.UUID: run_uuid,
            ctx_keys.NAMESPACE: namespace,
            ctx_keys.ITERATION: iteration,
            ctx_keys.CONTEXT_PATH: ctx_paths.CONTEXT_ROOT,
            ctx_keys.ARTIFACTS_PATH: ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ctx_keys.CREATED_AT: created_at,
            ctx_keys.COMPILED_AT: compiled_at,
            ctx_keys.SCHEDULE_AT: schedule_at,
            ctx_keys.STARTED_AT: started_at,
            ctx_keys.FINISHED_AT: finished_at,
            ctx_keys.DURATION: duration,
            ctx_keys.CLONING_KIND: cloning_kind,
            ctx_keys.ORIGINAL_UUID: original_uuid,
            ctx_keys.IS_INDEPENDENT: is_independent,
            ctx_keys.STORE_PATH: "",
        },
    }

    plugins = V1Plugins.get_or_create(plugins)
    if plugins.collect_artifacts:
        run_artifacts_path = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_path)
        run_outputs_path = ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format(run_path)
        resolved_contexts[ctx_sections.GLOBALS][
            ctx_keys.RUN_ARTIFACTS_PATH
        ] = run_artifacts_path
        resolved_contexts[ctx_sections.GLOBALS][
            ctx_keys.RUN_OUTPUTS_PATH
        ] = run_outputs_path
    elif artifacts_store:
        run_artifacts_path = os.path.join(artifacts_store.store_path, run_path)
        run_outputs_path = os.path.join(run_artifacts_path, "outputs")
        resolved_contexts[ctx_sections.GLOBALS][
            ctx_keys.RUN_ARTIFACTS_PATH
        ] = run_artifacts_path
        resolved_contexts[ctx_sections.GLOBALS][
            ctx_keys.RUN_OUTPUTS_PATH
        ] = run_outputs_path

    if plugins.mount_artifacts_store and artifacts_store:
        resolved_contexts[ctx_sections.GLOBALS][
            ctx_keys.STORE_PATH
        ] = artifacts_store.store_path
    return resolved_contexts


def resolve_contexts(
    namespace: str,
    owner_name: str,
    project_name: str,
    project_uuid: str,
    run_uuid: str,
    run_name: str,
    run_path: str,
    compiled_operation: V1CompiledOperation,
    artifacts_store: V1Connection,
    connection_by_names: Dict[str, V1Connection],
    iteration: int,
    created_at: datetime,
    compiled_at: datetime,
    schedule_at: Optional[datetime] = None,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    duration: Optional[float] = None,
    cloning_kind: V1CloningKind = None,
    original_uuid: Optional[str] = None,
    is_independent: bool = True,
) -> Dict:
    run_kind = compiled_operation.get_run_kind()
    if run_kind not in CONTEXTS_MANAGERS:
        raise PolyaxonCompilerError(
            "Contexts manager Error. "
            "Specification with run kind: {} is not supported in this deployment version".format(
                run_kind
            )
        )

    resolved_contexts = resolve_globals_contexts(
        namespace=namespace,
        owner_name=owner_name,
        project_name=project_name,
        project_uuid=project_uuid,
        run_uuid=run_uuid,
        run_name=run_name,
        run_path=run_path,
        iteration=iteration,
        created_at=created_at,
        compiled_at=compiled_at,
        schedule_at=schedule_at,
        started_at=started_at,
        finished_at=finished_at,
        duration=duration,
        plugins=compiled_operation.plugins,
        artifacts_store=artifacts_store,
        cloning_kind=cloning_kind,
        original_uuid=original_uuid,
        is_independent=is_independent,
    )

    return CONTEXTS_MANAGERS[run_kind].resolve(
        namespace=namespace,
        owner_name=owner_name,
        project_name=project_name,
        run_uuid=run_uuid,
        contexts=resolved_contexts,
        compiled_operation=compiled_operation,
        connection_by_names=connection_by_names,
    )
