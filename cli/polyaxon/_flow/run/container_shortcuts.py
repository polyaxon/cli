from collections.abc import Mapping
from copy import deepcopy
import math
from typing import Dict, List, Tuple, Union

from clipped.compact.pydantic import (
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
    validation_after,
    validation_before,
)
from clipped.config.patch_strategy import PatchStrategy
from clipped.utils.units import is_cpu_value, is_memory_value
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._vendor.k8s.quantity import parse_quantity


CmdShortcut = Union[StrictStr, List[StrictStr]]
EnvShortcut = Dict[StrictStr, StrictStr]
ResourcesShortcut = Dict[StrictStr, Union[StrictInt, StrictFloat, StrictStr]]
CONTAINER_SHORTCUT_FIELDS = ("cmd", "env", "resources")

_GPU = "gpu"
_NVIDIA_GPU = "nvidia.com/gpu"
_MAX_INT = 2**63  # Kubernetes quantities and orjson stop at 64-bit integers.
_QUANTITIES = {"cpu": is_cpu_value, "memory": is_memory_value}


def _is_count(value: str) -> bool:
    return value.isascii() and value.isdigit() and int(value) < _MAX_INT


def _parse_resource(key: str, value) -> Tuple:
    """Return the (request, limit) pair of one resources shortcut entry."""
    is_count = key not in _QUANTITIES
    is_valid = _QUANTITIES.get(key, _is_count)
    error = "resources.{} {}".format
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(error(key, "must be a number or a range such as 1..2."))
    if not isinstance(value, str):
        if (isinstance(value, float) and not math.isfinite(value)) or value < 0:
            raise ValueError(error(key, "must be a finite non-negative number."))
        if value >= _MAX_INT:
            raise ValueError(error(key, "is too large."))
        if is_count and not isinstance(value, int):
            raise ValueError(error(key, "must be an integer count."))
        return (value, value) if is_count else (value, None)

    text = value.strip()
    is_range = ".." in text
    low, high = (p.strip() for p in text.split("..", 1)) if is_range else (text, "")
    if not low and not high:
        raise ValueError(error(key, "needs a request, a limit, or both."))
    for part in (low, high):
        if part and not is_valid(part):
            raise ValueError(
                error(
                    key,
                    "has an unsupported value `{}`; use container.resources for "
                    "other quantities or templates.".format(part),
                )
            )
    # Exact decimals; the reporting converters round fractional values.
    if low and high and parse_quantity(low) > parse_quantity(high):
        raise ValueError(error(key, "has a request greater than its limit."))
    low, high = ((int(p) if is_count else p) if p else None for p in (low, high))
    if not is_range:
        return (low, low) if is_count else (low, None)
    return low, high


def lower_resources(resources: Dict) -> Dict:
    """Container `requests`/`limits` of the resources shortcut; empty sides omitted."""
    lowered = {"requests": {}, "limits": {}}
    for key, value in resources.items():
        name = _NVIDIA_GPU if key == _GPU else key
        for side, quantity in zip(lowered, _parse_resource(key, value)):
            if quantity is not None:
                lowered[side][name] = quantity
    return {side: values for side, values in lowered.items() if values}


class ContainerShortcutsMixin(BaseSchemaModel):
    """Models declare the fields in place to preserve their serialized field order."""

    @field_validator("cmd", check_fields=False, **validation_after)
    @classmethod
    def validate_cmd(cls, cmd):
        if isinstance(cmd, str):
            if not cmd.strip():
                raise ValueError("cmd must not be blank.")
        elif cmd is not None:
            if not cmd:
                raise ValueError("cmd must not be empty.")
            for index, line in enumerate(cmd):
                if not line.strip():
                    raise ValueError("cmd[{}] must not be blank.".format(index))
        return cmd

    @field_validator("env", check_fields=False, **validation_before)
    @classmethod
    def validate_env(cls, env):
        if env is None:
            return env
        if not isinstance(env, Mapping):
            raise ValueError("env must be a mapping of names to string values.")
        for name, value in env.items():
            if isinstance(value, (bool, int, float)):
                literal = str(value).lower() if isinstance(value, bool) else value
                raise ValueError(
                    'env.{} must be a string; quote it: "{}".'.format(name, literal)
                )
        return env

    @field_validator("resources", check_fields=False, **validation_before)
    @classmethod
    def validate_resources(cls, resources):
        if resources is None:
            return resources
        if not isinstance(resources, Mapping):
            raise ValueError("resources must be a mapping of resource names to values.")
        if _NVIDIA_GPU in resources:
            raise ValueError("resources.nvidia.com/gpu is spelled gpu.")
        for key, value in resources.items():
            if key not in ("cpu", "memory", _GPU) and not (
                isinstance(key, str) and "/" in key
            ):
                raise ValueError(
                    "Unknown resource `{}`; use cpu, memory, gpu, or an extended "
                    "resource such as google.com/tpu.".format(key)
                )
            _parse_resource(key, value)
        return resources

    @classmethod
    def patch_obj(cls, config, values, strategy=None, *, fields=None):
        strategy = strategy or PatchStrategy.POST_MERGE
        keys = set(type(config).model_fields if fields is None else fields)
        # Generic list merging would mix or split scripts, so cmd never reaches it.
        result = super().patch_obj(config, values, strategy, fields=keys - {"cmd"})
        if "cmd" in keys and "cmd" in getattr(values, "model_fields_set", ()):
            # A list of shell lines is a single script across authored overlays.
            if config.cmd is None or strategy in (
                PatchStrategy.POST_MERGE,
                PatchStrategy.REPLACE,
            ):
                result.cmd = deepcopy(values.cmd)
        return result
