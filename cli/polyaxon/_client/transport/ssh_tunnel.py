import websocket

from clipped.utils.encoding import BytesLike, as_bytes
from polyaxon._sandbox.client_utils import parse_error_message
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
        raise PolyaxonClientException(
            "ssh tunnel websocket handshake failed: {}".format(message)
        ) from None
    except websocket.WebSocketException as e:
        raise PolyaxonClientException(
            "ssh tunnel websocket open failed: {}".format(e)
        ) from e


class SandboxSshTunnelClient:
    def __init__(self, url: str, headers=None, timeout=None):
        self._ws = connect(url=url, headers=headers, timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def send(self, data: BytesLike):
        try:
            self._ws.send(as_bytes(data), opcode=OPCODE_BINARY)
        except websocket.WebSocketException as e:
            raise PolyaxonClientException(
                "ssh tunnel websocket send failed: {}".format(e)
            ) from e

    def recv(self) -> bytes:
        while True:
            try:
                opcode, data = self._ws.recv_data()
            except websocket.WebSocketException as e:
                raise PolyaxonClientException(
                    "ssh tunnel websocket recv failed: {}".format(e)
                ) from e

            if opcode == OPCODE_BINARY:
                return data
            if opcode == OPCODE_CLOSE:
                return b""
            if opcode in (OPCODE_PING, OPCODE_PONG):
                continue
            if opcode == OPCODE_TEXT:
                raise PolyaxonClientException(
                    "SSH tunnel received an unsupported text websocket frame."
                )
            raise PolyaxonClientException("SSH tunnel received an unsupported frame.")

    def close(self):
        try:
            self._ws.close()
        except websocket.WebSocketException:
            pass
