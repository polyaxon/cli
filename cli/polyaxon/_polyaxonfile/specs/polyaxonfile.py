from collections.abc import Mapping
from copy import deepcopy
from typing import Dict, Optional, Union

from clipped.config.patch_strategy import PatchStrategy
from clipped.utils.bools import to_bool
from polyaxon._config.spec import ConfigSpec
from polyaxon._flow.base import BaseOp
from polyaxon._flow.polyaxonfile import (
    PartialV1Polyaxonfile,
    V1Polyaxonfile,
    get_polyaxonfile_model,
)
from polyaxon._flow.run.patch import patch_run, validate_run_patch
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon.exceptions import PolyaxonfileError


_ATOMIC_TYPES = frozenset({type(None), bool, int, float, complex, str, bytes})
_MODEL_COPY_HOOKS = {
    name: getattr(BaseSchemaModel, name, None)
    for name in (
        "__deepcopy__",
        "__copy__",
        "copy",
        "model_copy",
        "__getstate__",
        "__setstate__",
        "__reduce__",
        "__reduce_ex__",
    )
}


def _copy_model_value(value, memo):
    """Copy model state without dispatching immutable fields through deepcopy."""
    value_type = type(value)
    if value_type in _ATOMIC_TYPES:
        return value
    key = id(value)
    if key in memo:
        return memo[key]

    if value_type is dict:
        result = {}
        memo[key] = result
        for k, v in value.items():
            if type(k) not in _ATOMIC_TYPES:
                k = _copy_model_value(k, memo)
            if type(v) not in _ATOMIC_TYPES:
                v = _copy_model_value(v, memo)
            result[k] = v
    elif value_type is list:
        result = []
        memo[key] = result
        result.extend(_copy_model_value(item, memo) for item in value)
    elif value_type is set and all(type(item) in _ATOMIC_TYPES for item in value):
        result = value.copy()
        memo[key] = result
    elif isinstance(value, BaseSchemaModel) and all(
        getattr(value_type, name, None) is method
        for name, method in _MODEL_COPY_HOOKS.items()
    ):
        attributes = value.__dict__
        fields_set = value.model_fields_set
        shallow = (
            not value.__private_attributes__
            and not getattr(value, "__pydantic_extra__", None)
            and id(attributes) not in memo
            and id(fields_set) not in memo
        )
        result = value.model_copy() if shallow else value_type.__new__(value_type)
        memo[key] = result
        if shallow:
            memo[id(fields_set)] = result.model_fields_set
        # Attribute names are strings; only their mutable values need recursion.
        if id(attributes) not in memo:
            copied_attributes = result.__dict__ if shallow else attributes.copy()
            memo[id(attributes)] = copied_attributes
            for name, item in attributes.items():
                if type(item) not in _ATOMIC_TYPES:
                    copied_attributes[name] = _copy_model_value(item, memo)
        if not shallow:
            result.__setstate__(_copy_model_value(value.__getstate__(), memo))
    else:
        return deepcopy(value, memo)

    # State dictionaries are temporary; keep their IDs from being reused in memo.
    memo.setdefault(id(memo), []).append(value)
    return result


def read_polyaxonfile(
    values, partial: bool = False, is_preset: bool = False
) -> V1Polyaxonfile:
    """Read one authored document without resolving references or merging layers."""
    if isinstance(values, V1Polyaxonfile):
        config = _copy_model_value(values, {})
    else:
        source = ConfigSpec.get_from(values)
        source.check_type()
        values = source.read()
        if not isinstance(values, Mapping):
            raise PolyaxonfileError("The Polyaxonfile must contain a mapping.")

        model = (
            PartialV1Polyaxonfile
            if partial or is_preset
            else get_polyaxonfile_model(values.get("kind"))
        )
        config = model.from_dict(deepcopy(values))
    if is_preset:
        config.is_preset = True
    return config


def compose_polyaxonfile(
    local: Union[Dict, V1Polyaxonfile],
    run_patch_strategy: Optional[PatchStrategy] = None,
    is_dag_node: bool = False,
) -> V1Polyaxonfile:
    """Compose collected sources without changing the authored document."""
    # Only mappings are read; nested components are already models.
    if isinstance(local, Mapping):
        local = read_polyaxonfile(local)
    component = local.component
    # Own mutable layers once; shared Python objects must not alias their base.
    values = {
        key: getattr(local, key)
        for key in type(local).get_model_fields()
        if key != "component"
    }
    if any(type(value) not in _ATOMIC_TYPES for value in values.values()):
        local = type(local).model_construct(
            _fields_set=local.model_fields_set - {"component"},
            **_copy_model_value(values, {}),
        )
    effective = (
        compose_polyaxonfile(component) if component is not None else V1Polyaxonfile()
    )
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
        "container",
        "cmd",
        "env",
        "run_patch",
        "strict_params",
        "version",
    }
    BaseOp.patch_obj(effective, local, strategy=strategy, fields=patch_fields)
    effective.strict_params = strict_params
    if effective.version is None and local.version is not None:
        effective.version = local.version

    if "run" in local.model_fields_set:
        effective.run = patch_run(effective.run, local.run, strategy)

    # Root shortcuts patch the main container before this layer's runPatch.
    effective.run = local.apply_shortcuts(effective.run, run_patch_strategy or strategy)

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
            setattr(effective, field, deepcopy(getattr(local, field)))
    return effective
