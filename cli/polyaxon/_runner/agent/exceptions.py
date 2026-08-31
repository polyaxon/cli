import re
from typing import Any


MAX_EXCEPTION_BODY_LENGTH = 2000

_SENSITIVE_KEY_PATTERN = (
    r"authorization|cookie|password|secret|token|api[_-]?key|"
    r"private[_-]?key|client[_-]?secret"
)
_SENSITIVE_QUOTED_VALUE_REGEX = re.compile(
    (
        r"([\"']?)"
        r"({})"
        r"([\"']?\s*[:=]\s*)"
        r"([\"'])"
        r"((?:\\.|(?!\4).)*)"
        r"\4"
    ).format(_SENSITIVE_KEY_PATTERN),
    re.IGNORECASE,
)
_SENSITIVE_UNQUOTED_BEARER_VALUE_REGEX = re.compile(
    (
        r"([\"']?)"
        r"({})"
        r"([\"']?\s*[:=]\s*)"
        r"Bearer\s+"
        r"([^\n,;\"'}}\]]+)"
    ).format(_SENSITIVE_KEY_PATTERN),
    re.IGNORECASE,
)
_SENSITIVE_UNQUOTED_VALUE_REGEX = re.compile(
    (
        r"([\"']?)"
        r"({})"
        r"([\"']?\s*[:=]\s*)"
        r"([^\s,\"'}}]+)"
        r"([\"']?)"
    ).format(_SENSITIVE_KEY_PATTERN),
    re.IGNORECASE,
)


def _to_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _redact_sensitive_values(value: str) -> str:
    value = _SENSITIVE_QUOTED_VALUE_REGEX.sub(
        lambda m: "{}{}{}{}<redacted>{}".format(
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(4),
            m.group(4),
        ),
        value,
    )
    value = _SENSITIVE_UNQUOTED_BEARER_VALUE_REGEX.sub(
        lambda m: "{}{}{}<redacted>".format(
            m.group(1),
            m.group(2),
            m.group(3),
        ),
        value,
    )
    return _SENSITIVE_UNQUOTED_VALUE_REGEX.sub(
        lambda m: "{}{}{}<redacted>{}".format(
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(5),
        ),
        value,
    )


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return "{}...<truncated {} chars>".format(
        value[:max_length], len(value) - max_length
    )


def _clean_body(value: Any, max_length: int) -> str:
    return _truncate(_redact_sensitive_values(_to_text(value)), max_length)


def format_agent_exception(
    exc: Exception,
    max_body_length: int = MAX_EXCEPTION_BODY_LENGTH,
) -> str:
    status = getattr(exc, "status", None)
    reason = getattr(exc, "reason", None)
    body = getattr(exc, "body", None)

    parts = []
    if status is not None:
        parts.append("status={}".format(status))
    if reason:
        parts.append("reason={}".format(reason))
    if body:
        parts.append("body={}".format(_clean_body(body, max_body_length)))

    exc_name = exc.__class__.__name__
    if parts:
        return "{}({})".format(exc_name, ", ".join(parts))

    message = str(exc).strip()
    if message:
        return "{}: {}".format(exc_name, _truncate(message, max_body_length))
    return repr(exc)
