from collections.abc import Mapping
import copy
from typing import Dict, List, Optional, Union

from clipped.config.patch_strategy import PatchStrategy
from clipped.utils.bools import to_bool
from polyaxon._config.spec import ConfigSpec
from polyaxon._env_vars.getters.queue import get_queue_info
from polyaxon._flow.base import BaseOp
from polyaxon._flow.init import V1Init
from polyaxon._flow.matrix.enums import V1MatrixKind
from polyaxon._flow.matrix.matrix import V1Matrix
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._flow.run.patch import patch_run, patch_run_patch, validate_run_patch
from polyaxon._polyaxonfile.specs import (
    CompiledOperationSpecification,
    OperationSpecification,
    get_specification,
    kinds,
    read_polyaxonfile,
)
from polyaxon.exceptions import PolyaxonfileError


def patch_polyaxonfile(
    config: V1Polyaxonfile,
    preset_files: List[Union[str, Dict, V1Polyaxonfile]],
) -> V1Polyaxonfile:
    """Merge file overlays, keeping the source and runPatch for composition."""
    config = read_polyaxonfile(config)
    run_patches = []
    for preset_file in preset_files:
        if isinstance(preset_file, V1Polyaxonfile):
            preset = read_polyaxonfile(preset_file, is_preset=True)
        else:
            values = copy.deepcopy(ConfigSpec.read_from(preset_file))
            run = values.get("run")
            if isinstance(run, Mapping) and "kind" not in run:
                native_run = config.run
                if native_run is None and config.component is not None:
                    native_run = config.component.get_native_run()
                if native_run is not None:
                    values["run"] = {"kind": native_run.kind, **run}
            preset = read_polyaxonfile(values, is_preset=True)

        strategy = preset.patch_strategy or PatchStrategy.POST_MERGE
        fields = preset.model_fields_set - set(V1Polyaxonfile._FIELDS_MANUAL_PATCH)
        config.patch(
            V1Polyaxonfile.model_construct(
                **{key: getattr(preset, key) for key in fields}
            ),
            strategy=strategy,
        )
        if "run" in preset.model_fields_set:
            config.run = patch_run(config.run, preset.run, strategy)
        if preset.run_patch is not None:
            run_patches.append((preset.run_patch, strategy))

    # The final native runtime supplies the type for all retained runPatch layers.
    # Applying runPatch to run here would change precedence against later files.
    if run_patches:
        run = config.get_native_run()
        replica_types = (
            run.get_replica_types()
            if run is not None and hasattr(run, "get_replica_types")
            else None
        )
        for value, strategy in run_patches:
            config.run_patch = patch_run_patch(
                current=config.run_patch,
                value=value,
                kind=run.kind if run is not None else None,
                replica_types=replica_types,
                strategy=strategy,
            )
    return config


def compose_polyaxonfile(
    config: Union[Dict, V1Polyaxonfile],
    run_patch_strategy: Optional[PatchStrategy] = None,
    is_dag_node: bool = False,
) -> V1Polyaxonfile:
    """Compose collected sources without changing the authored document."""
    if isinstance(config, V1Polyaxonfile):
        values = {key: getattr(config, key) for key in config.model_fields_set}
    elif isinstance(config, Mapping):
        values = dict(config)
    else:
        raise PolyaxonfileError("Composition requires a mapping or a V1Polyaxonfile.")

    component = values.pop("component", None)
    effective = (
        compose_polyaxonfile(component) if component is not None else V1Polyaxonfile()
    )
    run = values.get("run")
    if isinstance(run, Mapping) and "kind" not in run and effective.run is not None:
        values["run"] = {"kind": effective.run.kind, **run}

    local = read_polyaxonfile(values)
    if is_dag_node and local.schedule is not None:
        raise PolyaxonfileError(
            "DAG node `{}` cannot define a schedule.".format(local.name)
        )
    if component is None and any(
        (local.hub_ref, local.path_ref, local.url_ref, local.dag_ref)
    ):
        raise PolyaxonfileError(
            "Collect the Polyaxonfile reference before composing its local fields."
        )
    strategy = local.patch_strategy or PatchStrategy.POST_MERGE
    strict_params = to_bool(effective.strict_params, handle_none=True) or to_bool(
        local.strict_params, handle_none=True
    )
    patch_fields = local.model_fields_set - {
        "component",
        "hub_ref",
        "path_ref",
        "url_ref",
        "dag_ref",
        "is_preset",
        "patch_strategy",
        "run",
        "run_patch",
        "strict_params",
        "version",
    }
    BaseOp.patch_obj(
        effective,
        V1Polyaxonfile.model_construct(
            **{key: getattr(local, key) for key in patch_fields}
        ),
        strategy=strategy,
    )
    effective.strict_params = strict_params
    if effective.version is None and local.version is not None:
        effective.version = local.version

    if "run" in local.model_fields_set:
        effective.run = patch_run(effective.run, local.run, strategy)

    if local.run_patch:
        if effective.run is None:
            raise PolyaxonfileError("runPatch requires a resolved runtime.")
        effective.run.patch(
            validate_run_patch(
                local.run_patch,
                effective.run.kind,
                replica_types=effective.get_replica_types(),
            ),
            strategy=run_patch_strategy or strategy,
        )
    if is_dag_node:
        for field in (
            "name",
            "dependencies",
            "trigger",
            "conditions",
            "joins",
            "skip_on_upstream_skip",
            "schedule",
        ):
            setattr(effective, field, copy.deepcopy(getattr(local, field)))
    return effective


def get_op_specification(
    config: Optional[V1Polyaxonfile] = None,
    hub: Optional[str] = None,
    params: Optional[Dict] = None,
    hparams: Optional[Dict] = None,
    matrix_kind: Optional[str] = None,
    matrix_concurrency: Optional[int] = None,
    matrix_num_runs: Optional[int] = None,
    matrix: Optional[Union[Dict, V1Matrix]] = None,
    presets: Optional[List[str]] = None,
    queue: Optional[str] = None,
    namespace: Optional[str] = None,
    nocache: Optional[bool] = None,
    cache: Optional[Union[int, str, bool]] = None,
    approved: Optional[Union[int, str, bool]] = None,
    validate_params: bool = True,
    preset_files: Optional[List[str]] = None,
    git_init: Optional[V1Init] = None,
    strict_params: Optional[bool] = None,
) -> V1Operation:
    if cache and nocache:
        raise PolyaxonfileError("Received both 'cache' and 'nocache'")
    op_data = {"kind": kinds.OPERATION}
    if config and config.version is not None:
        op_data["version"] = config.version
    if params:
        if not isinstance(params, Mapping):
            raise PolyaxonfileError(
                "Params: `{}` must be a valid mapping".format(params)
            )
        op_data["params"] = params
    if hparams:
        if not isinstance(hparams, Mapping):
            raise PolyaxonfileError(
                "Hyper-Params: `{}` must be a valid mapping".format(hparams)
            )
        op_data["matrix"] = {
            "kind": matrix_kind or V1MatrixKind.GRID,
            "concurrency": matrix_concurrency or 1,
            "params": hparams,
        }
        if matrix_num_runs:
            op_data["matrix"]["numRuns"] = matrix_num_runs
    if matrix:
        op_data["matrix"] = (
            matrix if isinstance(matrix, Mapping) else matrix.to_light_dict()
        )
    if presets:
        op_data["presets"] = presets
    if queue:
        # Check only
        get_queue_info(queue)
        op_data["queue"] = queue
    if namespace:
        op_data["namespace"] = namespace
    if cache is not None:
        op_data["cache"] = {"disable": not to_bool(cache)}
    if nocache:
        op_data["cache"] = {"disable": True}
    # Handle approval logic
    if approved is not None:
        op_data["isApproved"] = to_bool(approved)
    if strict_params is not None:
        op_data["strictParams"] = strict_params

    if config and (hub or config.kind == kinds.COMPONENT):
        op_data["component"] = config.to_dict(exclude_none=False)
        config = get_specification(data=[op_data])
    elif config and config.kind in (None, kinds.OPERATION):
        config = get_specification(data=[config.to_dict(exclude_none=False), op_data])
    elif hub:
        op_data["hubRef"] = hub
        config = get_specification(data=[op_data])

    if hub and config.hub_ref is None:
        config.hub_ref = hub

    # Check if there's presets
    config = patch_polyaxonfile(config, preset_files or [])
    # Turn git_init to a pre_merge preset
    if git_init:
        git_preset = V1Operation(
            run_patch={"init": [git_init.to_dict()]}, is_preset=True
        )
        config = config.patch(git_preset, strategy=PatchStrategy.PRE_MERGE)

    # Sanity check if params were passed and we are not dealing with a hub component
    if validate_params:
        run_config, params = OperationSpecification.compile_operation_with_params(
            config
        )
        run_config.validate_params(params=params, is_template=False)
        if run_config.is_dag_run:
            CompiledOperationSpecification.apply_operation_contexts(run_config)
    return config
