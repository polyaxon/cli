import jinja2

from typing import Any, Dict, Optional

from markupsafe import soft_str

from polyaxon.exceptions import PolyaxonSchemaError


def map_format(value, pattern, variable_name: Optional[str] = None):
    if variable_name:
        return soft_str(pattern) % {variable_name: value}
    return soft_str(pattern) % value


def get_engine():
    env = jinja2.Environment()
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
    except (jinja2.exceptions.TemplateError, ValueError, TypeError) as e:
        raise PolyaxonSchemaError(
            f"Encountered a problem rendering the template, "
            f"please make sure your variables are resolvable. "
            f"Error: {repr(e)}"
        )


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
