from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Dict, List, Optional

from clipped.utils.json import orjson_loads


@dataclass(frozen=True)
class FsReadResult:
    data: bytes
    next_offset: int
    eof: bool


@dataclass(frozen=True)
class FsWriteResult:
    path: str
    bytes_written: int
    created: bool


def normalize_command(command: Sequence[str]) -> List[str]:
    if isinstance(command, str):
        raise TypeError("command must be a sequence of strings, not a string")
    try:
        value = list(command)
    except TypeError as e:
        raise TypeError("command must be a sequence of strings") from e
    if not value:
        raise ValueError("command must not be empty")
    if not all(isinstance(item, str) for item in value):
        raise TypeError("command must contain only strings")
    return value


def normalize_env(env: Optional[Mapping[str, Optional[str]]]) -> Optional[Dict]:
    if env is None:
        return None
    if not isinstance(env, Mapping):
        raise TypeError("env must be a mapping")

    value = {}
    for key, item in env.items():
        if not isinstance(key, str):
            raise TypeError("env keys must be strings")
        if item is not None and not isinstance(item, str):
            raise TypeError(
                "env values must be strings or None, got {} for key {!r}".format(
                    type(item).__name__,
                    key,
                )
            )
        value[key] = item
    return value


def format_mode(mode: int) -> str:
    if isinstance(mode, bool) or not isinstance(mode, int):
        raise TypeError("mode must be an int")
    if mode < 0 or mode > 0o777:
        raise ValueError("mode must be between 0o000 and 0o777")
    return "{:04o}".format(mode)


def parse_error_message(data: bytes, fallback: str) -> str:
    try:
        payload = orjson_loads(data or b"{}")
    except Exception:
        return fallback

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict) and error.get("message"):
        return error["message"]
    if isinstance(payload, dict) and payload.get("message"):
        return payload["message"]
    return fallback
