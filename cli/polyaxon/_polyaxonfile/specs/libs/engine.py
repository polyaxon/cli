from datetime import date, datetime
import jinja2
from jinja2 import meta
from jinja2.runtime import Macro
from jinja2.sandbox import ImmutableSandboxedEnvironment, safe_range
from jinja2.utils import Namespace
import re
from types import BuiltinMethodType
from typing import Any, Dict, Optional, Type

from markupsafe import soft_str

from polyaxon.exceptions import PolyaxonSchemaError


MAX_POWER_BITS = 4096
MAX_REPEAT_ITEMS = 100000
MAX_NAME_LENGTH = 128
_UNSUPPORTED_NAME_CHARS = re.compile(r"[^A-Za-z0-9_-]+")

_SAFE_GLOBALS = {"range": safe_range, "dict": dict, "namespace": Namespace}
_READ_ONLY_METHODS = (
    (
        str,
        frozenset(
            {
                "lower",
                "upper",
                "strip",
                "lstrip",
                "rstrip",
                "split",
                "rsplit",
                "replace",
                "startswith",
                "endswith",
                "join",
            }
        ),
    ),
    (dict, frozenset({"get", "items", "keys", "values"})),
    (date, frozenset({"isoformat", "strftime"})),
    (datetime, frozenset({"isoformat", "strftime"})),
)


class _TemplateEnvironment(ImmutableSandboxedEnvironment):
    intercepted_binops = frozenset({"*", "**"})

    def unsafe_undefined(self, obj, attribute):
        raise jinja2.exceptions.SecurityError(
            f"Access to attribute {attribute!r} is not allowed."
        )

    def is_safe_callable(self, obj):
        if not super().is_safe_callable(obj):
            return False
        if any(obj is helper for helper in _SAFE_GLOBALS.values()):
            return True
        if isinstance(obj, Macro):
            return True
        if isinstance(obj, BuiltinMethodType):
            return any(
                isinstance(obj.__self__, receiver_type) and obj.__name__ in methods
                for receiver_type, methods in _READ_ONLY_METHODS
            )
        return False

    def call_binop(self, context, operator, left, right):
        if operator == "**":
            if (
                isinstance(left, int)
                and isinstance(right, int)
                and abs(left) > 1
                and right > 0
            ):
                if (abs(left).bit_length() - 1) * right >= MAX_POWER_BITS:
                    raise jinja2.exceptions.SecurityError(
                        "Power exceeds the template limit."
                    )
                if abs(left).bit_length() * right > MAX_POWER_BITS:
                    result = left**right
                    if result.bit_length() > MAX_POWER_BITS:
                        raise jinja2.exceptions.SecurityError(
                            "Power exceeds the template limit."
                        )
                    return result
        elif operator == "*":
            if isinstance(left, int) and isinstance(right, int) and left and right:
                total_bits = abs(left).bit_length() + abs(right).bit_length()
                if total_bits - 1 > MAX_POWER_BITS:
                    raise jinja2.exceptions.SecurityError(
                        "Integer multiplication exceeds the template limit."
                    )
                if total_bits > MAX_POWER_BITS:
                    result = left * right
                    if result.bit_length() > MAX_POWER_BITS:
                        raise jinja2.exceptions.SecurityError(
                            "Integer multiplication exceeds the template limit."
                        )
                    return result
            sequence, count = left, right
            if isinstance(left, int) and isinstance(right, (str, list, tuple)):
                sequence, count = right, left
            if (
                isinstance(sequence, (str, list, tuple))
                and isinstance(count, int)
                and count > 0
                and len(sequence) * count > MAX_REPEAT_ITEMS
            ):
                raise jinja2.exceptions.SecurityError(
                    "Sequence repetition exceeds the template limit."
                )
        return super().call_binop(context, operator, left, right)


def map_format(value, pattern, variable_name: Optional[str] = None):
    if variable_name:
        return soft_str(pattern) % {variable_name: value}
    return soft_str(pattern) % value


def get_engine(undefined: Type[jinja2.Undefined] = jinja2.Undefined):
    env = _TemplateEnvironment(undefined=undefined)
    env.globals.clear()
    env.globals.update(_SAFE_GLOBALS)
    env.filters["map_format"] = map_format
    return env


def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """
    Render a Jinja2 template string with context.

    Args:
        template_str: Template string with Jinja2 syntax
        context: Dictionary of variables for template rendering

    Returns:
        Rendered string

    Raises:
        PolyaxonSchemaError: If template rendering fails
    """
    if not template_str or not isinstance(template_str, str):
        return template_str

    if "{{" not in template_str and "{%" not in template_str:
        return template_str  # No template syntax, return as-is

    try:
        engine = get_engine()
        template = engine.from_string(template_str)
        return template.render(**context)
    except (jinja2.exceptions.TemplateError, ValueError, TypeError, OverflowError) as e:
        raise PolyaxonSchemaError(
            f"Encountered a problem rendering the template, "
            f"please make sure your variables are resolvable. "
            f"Error: {repr(e)}"
        )


def render_text_strict(template_str: str, context: Dict[str, Any], field: str) -> str:
    """Render once as text; unknown variables are errors, not empty strings."""
    engine = get_engine(undefined=jinja2.StrictUndefined)
    try:
        parsed = engine.parse(template_str)
        unavailable = meta.find_undeclared_variables(parsed) - set(context)
        if unavailable:
            names = ", ".join(sorted(unavailable))
            raise PolyaxonSchemaError(f"`{field}` uses unavailable variables: {names}.")
        return engine.from_string(template_str).render(**context)
    except jinja2.exceptions.UndefinedError as e:
        raise PolyaxonSchemaError(f"`{field}` uses an unavailable variable: {e}.")
    except (
        jinja2.exceptions.TemplateError,
        ValueError,
        TypeError,
        ArithmeticError,
    ) as e:
        raise PolyaxonSchemaError(f"Could not render `{field}`: {repr(e)}")


def normalize_name(value: str) -> str:
    return _UNSUPPORTED_NAME_CHARS.sub("_", value).strip("_-")


def render_name_template(template_str: str, context: Dict[str, Any]) -> str:
    name = normalize_name(render_text_strict(template_str, context, field="name"))
    if not name:
        raise PolyaxonSchemaError(
            f"`name` template `{template_str}` rendered an empty run name."
        )
    if len(name) > MAX_NAME_LENGTH:
        name = name[: MAX_NAME_LENGTH - 2].rstrip("_-") + "--"
    return name


def render_config(config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively render all string values in a config dict.

    Args:
        config: Configuration dictionary with potential template strings
        context: Dictionary of variables for template rendering

    Returns:
        Config with all template strings rendered
    """
    if not config:
        return config

    rendered = {}
    for key, value in config.items():
        if isinstance(value, str):
            rendered[key] = render_template(value, context)
        elif isinstance(value, dict):
            rendered[key] = render_config(value, context)
        elif isinstance(value, list):
            rendered[key] = [
                render_config(item, context)
                if isinstance(item, dict)
                else render_template(item, context)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            rendered[key] = value
    return rendered
