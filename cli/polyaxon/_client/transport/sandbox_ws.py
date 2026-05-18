import websocket

from clipped.utils.encoding import BytesLike, as_bytes
from clipped.utils.json import orjson_dumps
from polyaxon._sandbox.client_utils import parse_error_message, parse_ws_event
from polyaxon.exceptions import PolyaxonClientException


OPCODE_TEXT = websocket.ABNF.OPCODE_TEXT
OPCODE_BINARY = websocket.ABNF.OPCODE_BINARY
OPCODE_CLOSE = websocket.ABNF.OPCODE_CLOSE
OPCODE_PING = websocket.ABNF.OPCODE_PING
OPCODE_PONG = websocket.ABNF.OPCODE_PONG


def _format_headers(headers):
    return ["{}: {}".format(k, v) for k, v in (headers or {}).items()]


def connect(url: str, headers=None, timeout=None):
    try:
        return websocket.create_connection(
            url,
            header=_format_headers(headers),
            timeout=timeout,
        )
    except websocket.WebSocketBadStatusException as e:
        message = parse_error_message(
            getattr(e, "resp_body", None),
            "websocket handshake failed with status {}".format(
                getattr(e, "status_code", "unknown")
            ),
        )
        raise PolyaxonClientException("pty.attach failed: {}".format(message)) from None
    except websocket.WebSocketException as e:
        raise PolyaxonClientException("pty.attach failed: {}".format(e)) from e


def recv_message(ws):
    while True:
        try:
            opcode, data = ws.recv_data()
        except websocket.WebSocketException as e:
            raise PolyaxonClientException(
                "pty websocket recv failed: {}".format(e)
            ) from e

        if opcode == OPCODE_BINARY:
            return data
        if opcode == OPCODE_TEXT:
            return parse_ws_event(data)
        if opcode == OPCODE_CLOSE:
            raise PolyaxonClientException("PTY websocket closed.")
        if opcode in (OPCODE_PING, OPCODE_PONG):
            continue
        raise PolyaxonClientException("Unsupported PTY websocket frame.")


class SandboxPtyWSClient:
    def __init__(self, ws, attached_event, resize=None, signal=None):
        self._ws = ws
        self._attached_event = attached_event
        self._resize = resize
        self._signal = signal

    @property
    def attached_event(self):
        return self._attached_event

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def send_stdin(self, data: BytesLike):
        try:
            self._ws.send(as_bytes(data), opcode=OPCODE_BINARY)
        except websocket.WebSocketException as e:
            raise PolyaxonClientException(
                "pty websocket send failed: {}".format(e)
            ) from e

    def send_control(self, event):
        try:
            self._ws.send(orjson_dumps(event), opcode=OPCODE_TEXT)
        except websocket.WebSocketException as e:
            raise PolyaxonClientException(
                "pty websocket send failed: {}".format(e)
            ) from e

    def recv(self):
        return recv_message(self._ws)

    def resize(self, cols: int, rows: int):
        if not self._resize:
            raise PolyaxonClientException("PTY resize callback is not configured.")
        return self._resize(cols, rows)

    def signal(self, signal: str):
        if not self._signal:
            raise PolyaxonClientException("PTY signal callback is not configured.")
        return self._signal(signal)

    def kill(self, signal: str = "SIGTERM"):
        return self.signal(signal)

    def close(self):
        try:
            self._ws.close()
        except websocket.WebSocketException as e:
            raise PolyaxonClientException(
                "pty websocket close failed: {}".format(e)
            ) from e
