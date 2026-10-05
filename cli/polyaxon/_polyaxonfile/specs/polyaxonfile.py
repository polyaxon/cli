from collections.abc import Mapping
from copy import deepcopy

from polyaxon._config.spec import ConfigSpec
from polyaxon._flow.component.component import V1Component
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.polyaxonfile import PartialV1Polyaxonfile, V1Polyaxonfile
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

        model = {
            "component": V1Component,
            "operation": V1Operation,
        }.get(values.get("kind"), V1Polyaxonfile)
        if partial or is_preset:
            model = PartialV1Polyaxonfile
        config = model.from_dict(deepcopy(values))
    if is_preset:
        config.is_preset = True
    return config
