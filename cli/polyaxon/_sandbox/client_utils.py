from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import posixpath
from typing import Dict, List, Optional

from clipped.utils.json import orjson_loads
from polyaxon.exceptions import PolyaxonClientException


MAX_REMOTE_PATH_BYTES = 4096


def parse_ws_event(data) -> Dict:
    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8")
        except UnicodeDecodeError as e:
            raise PolyaxonClientException(
                "Invalid PTY websocket event encoding."
            ) from e
    if not isinstance(data, str):
        raise PolyaxonClientException("Invalid PTY websocket text frame.")
    try:
        payload = orjson_loads(data.encode("utf-8"))
    except Exception as e:
        raise PolyaxonClientException("Invalid PTY websocket event JSON.") from e
    if not isinstance(payload, dict):
        raise PolyaxonClientException("Invalid PTY websocket event payload.")
    return payload


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


@dataclass(frozen=True)
class SandboxBgOutput:
    stdout: str
    stderr: str


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


def validate_remote_path(path: str) -> str:
    """Validate a POSIX path inside the sandbox container."""
    if not isinstance(path, str):
        raise TypeError("path must be a string")
    if not path:
        raise ValueError("path is required")
    if not posixpath.isabs(path):
        raise ValueError("path must be absolute")
    if "\x00" in path:
        raise ValueError("path contains NUL")
    if len(path.encode("utf-8")) > MAX_REMOTE_PATH_BYTES:
        raise ValueError("path exceeds {} bytes".format(MAX_REMOTE_PATH_BYTES))
    return path


class SseFrameBuffer:
    def __init__(self):
        self._buffer = bytearray()

    def feed(self, chunk: bytes) -> List[Dict]:
        self._buffer.extend(bytes(chunk))
        events = []

        while True:
            marker = self._buffer.find(b"\n\n")
            if marker < 0:
                break
            frame = bytes(self._buffer[:marker])
            del self._buffer[: marker + 2]
            event = self._parse_frame(frame)
            if event is not None:
                events.append(event)

        return events

    @staticmethod
    def _parse_frame(frame: bytes) -> Optional[Dict]:
        if not frame:
            return None

        try:
            text = frame.decode("utf-8")
        except UnicodeDecodeError as e:
            raise PolyaxonClientException("Invalid SSE event encoding.") from e

        event_type = "message"
        data_lines = []

        for line in text.split("\n"):
            if not line or line.startswith(":"):
                continue
            field, separator, value = line.partition(":")
            if separator and value.startswith(" "):
                value = value[1:]
            if field == "event":
                event_type = value
            elif field == "data":
                data_lines.append(value)

        if event_type == "ping" or not data_lines:
            return None

        data = "\n".join(data_lines)
        try:
            payload = orjson_loads(data.encode("utf-8"))
        except Exception as e:
            raise PolyaxonClientException(
                "Invalid SSE event JSON for event `{}`.".format(event_type)
            ) from e

        if not isinstance(payload, dict):
            raise PolyaxonClientException(
                "Invalid SSE event payload for event `{}`.".format(event_type)
            )

        event = dict(payload)
        event["type"] = event_type
        return event
