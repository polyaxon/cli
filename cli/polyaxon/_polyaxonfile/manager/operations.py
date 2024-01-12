import copy

from collections.abc import Mapping
from typing import Dict, List, Optional, Union

from clipped.config.patch_strategy import PatchStrategy
from clipped.utils.bools import to_bool

from polyaxon import pkg
from polyaxon._env_vars.getters.queue import get_queue_info
from polyaxon._flow import V1Component, V1Init, V1Matrix, V1MatrixKind, V1Operation
from polyaxon._polyaxonfile.specs import (
    CompiledOperationSpecification,
    OperationSpecification,
    get_specification,
    kinds,
)
from polyaxon.exceptions import PolyaxonfileError


def get_op_specification(
    config: Optional[Union[V1Component, V1Operation]] = None,
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
) -> V1Operation:
    if cache and nocache:
        raise PolyaxonfileError("Received both 'cache' and 'nocache'")
    op_data = {
        "version": config.version if config else pkg.SCHEMA_VERSION,
        "kind": kinds.OPERATION,
    }
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

    if config and config.kind == kinds.COMPONENT:
        op_data["component"] = config.to_dict()
        config = get_specification(data=[op_data])
    elif config and config.kind == kinds.OPERATION:
        config = get_specification(data=[config.to_dict(), op_data])
    elif hub:
        op_data["hubRef"] = hub
        config = get_specification(data=[op_data])

    if hub and config.hub_ref is None:
        config.hub_ref = hub

    # Check if there's presets
    for preset_plx_file in preset_files:
        preset_plx_file = OperationSpecification.read(preset_plx_file, is_preset=True)
        config = config.patch(preset_plx_file, strategy=preset_plx_file.patch_strategy)
    # Turn git_init to a pre_merge preset
    if git_init:
        git_preset = V1Operation(
            run_patch={"init": [git_init.to_dict()]}, is_preset=True
        )
        config = config.patch(git_preset, strategy=PatchStrategy.PRE_MERGE)

    # Sanity check if params were passed and we are not dealing with a hub component
    params = copy.deepcopy(config.params)
    if validate_params:
        # Avoid in-place patch
        run_config = get_specification(config.to_dict())
        run_config = OperationSpecification.compile_operation(run_config)
        run_config.validate_params(params=params, is_template=False)
        if run_config.is_dag_run:
            CompiledOperationSpecification.apply_operation_contexts(run_config)
    return config
