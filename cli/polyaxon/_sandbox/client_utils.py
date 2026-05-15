import base64
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import ssl
from typing import Dict, List, Optional, Union

from clipped.utils.json import orjson_loads


BytesLike = Union[bytes, bytearray, memoryview]


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


def as_bytes(data: BytesLike) -> bytes:
    if isinstance(data, str):
        raise TypeError("data must be bytes-like, not str")
    if isinstance(data, memoryview):
        return data.tobytes()
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    raise TypeError("data must be bytes-like")


def b64_data(data: Optional[BytesLike]) -> Optional[str]:
    if data is None:
        return None
    return base64.b64encode(as_bytes(data)).decode("ascii")


def parse_bool_header(value: Optional[str]) -> bool:
    return str(value or "").lower() == "true"


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


def parse_json(data: bytes):
    return orjson_loads(data or b"{}")


def get_requests_verify(sdk_config):
    if getattr(sdk_config, "verify_ssl", None) is False:
        return False
    return getattr(sdk_config, "ssl_ca_cert", None) or True


def get_requests_cert(sdk_config):
    cert_file = getattr(sdk_config, "cert_file", None)
    key_file = getattr(sdk_config, "key_file", None)
    if cert_file and key_file:
        return cert_file, key_file
    return cert_file


def build_async_ssl_context(sdk_config):
    if getattr(sdk_config, "verify_ssl", None) is False:
        return False

    context = ssl.create_default_context(
        cafile=getattr(sdk_config, "ssl_ca_cert", None)
    )
    if getattr(sdk_config, "assert_hostname", None) is False:
        context.check_hostname = False

    cert_file = getattr(sdk_config, "cert_file", None)
    if cert_file:
        context.load_cert_chain(
            cert_file,
            keyfile=getattr(sdk_config, "key_file", None),
        )
    return context
