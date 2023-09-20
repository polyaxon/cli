import jinja2

from typing import Optional

from markupsafe import soft_str


def map_format(value, pattern, variable_name: Optional[str] = None):
    if variable_name:
        return soft_str(pattern) % {variable_name: value}
    return soft_str(pattern) % value


def get_engine():
    env = jinja2.Environment()
    env.filters["map_format"] = map_format
    return env
