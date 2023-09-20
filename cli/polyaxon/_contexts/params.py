import re

PARAM_REGEX = re.compile(r"{{\s*(.+)\s*}}")


def is_template_ref(value: str) -> bool:
    try:
        value_parts = PARAM_REGEX.search(value)  # type: ignore[attr-defined]
        if value_parts:
            return True
    except Exception:  # noqa
        pass
    return False
