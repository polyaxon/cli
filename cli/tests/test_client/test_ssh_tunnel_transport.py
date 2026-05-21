import pytest
from unittest.mock import patch

from polyaxon._client.transport import ssh_tunnel
from polyaxon.exceptions import PolyaxonClientException


class FakeWS:
    def __init__(self, frames=None, send_error=None, recv_error=None, close_error=None):
        self.frames = list(frames or [])
        self.send_error = send_error
        self.recv_error = recv_error
        self.close_error = close_error
        self.sent = []
        self.closed = False

    def send(self, data, opcode):
        if self.send_error:
            raise self.send_error
        self.sent.append((opcode, data))

    def recv_data(self):
        if self.recv_error:
            raise self.recv_error
        return self.frames.pop(0)

    def close(self):
        self.closed = True
        if self.close_error:
            raise self.close_error


def test_ssh_tunnel_client_connects_with_headers_and_timeout():
    ws = FakeWS()

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        return_value=ws,
    ) as create_connection:
        client = ssh_tunnel.SandboxSshTunnelClient(
            url="wss://polyaxon/sandbox/v1/ns/owner/project/runs/uuid/ssh/tunnel",
            headers={"authorization": "Bearer token"},
            timeout=12,
        )

    assert client._ws is ws
    create_connection.assert_called_once_with(
        "wss://polyaxon/sandbox/v1/ns/owner/project/runs/uuid/ssh/tunnel",
        header=["authorization: Bearer token"],
        timeout=12,
    )


def test_ssh_tunnel_client_send_uses_binary_opcode():
    ws = FakeWS()

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        return_value=ws,
    ):
        client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    client.send(b"SSH bytes")

    assert ws.sent == [(ssh_tunnel.OPCODE_BINARY, b"SSH bytes")]


def test_ssh_tunnel_client_recv_returns_binary_bytes():
    ws = FakeWS(frames=[(ssh_tunnel.OPCODE_BINARY, b"output")])

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        return_value=ws,
    ):
        client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    assert client.recv() == b"output"


def test_ssh_tunnel_client_recv_returns_empty_bytes_on_close():
    ws = FakeWS(frames=[(ssh_tunnel.OPCODE_CLOSE, b"")])

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        return_value=ws,
    ):
        client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    assert client.recv() == b""


def test_ssh_tunnel_client_recv_skips_ping_and_pong():
    ws = FakeWS(
        frames=[
            (ssh_tunnel.OPCODE_PING, b""),
            (ssh_tunnel.OPCODE_PONG, b""),
            (ssh_tunnel.OPCODE_BINARY, b"output"),
        ]
    )

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        return_value=ws,
    ):
        client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    assert client.recv() == b"output"


def test_ssh_tunnel_client_recv_rejects_text_frames():
    ws = FakeWS(frames=[(ssh_tunnel.OPCODE_TEXT, b"not raw ssh")])

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        return_value=ws,
    ):
        client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    with pytest.raises(PolyaxonClientException, match="unsupported text"):
        client.recv()


def test_ssh_tunnel_client_wraps_handshake_status_errors():
    error = ssh_tunnel.websocket.WebSocketBadStatusException(
        "bad status",
        401,
        resp_body=b'{"error":{"message":"unauthorized"}}',
    )

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        side_effect=error,
    ):
        with pytest.raises(PolyaxonClientException, match="unauthorized"):
            ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")


def test_ssh_tunnel_client_wraps_open_send_and_recv_errors():
    ws_error = ssh_tunnel.websocket.WebSocketException("boom")

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        side_effect=ws_error,
    ):
        with pytest.raises(PolyaxonClientException, match="open failed"):
            ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    for method, match in (("send", "send failed"), ("recv", "recv failed")):
        kwargs = (
            {"send_error": ws_error} if method == "send" else {"recv_error": ws_error}
        )
        ws = FakeWS(**kwargs)
        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")
        with pytest.raises(PolyaxonClientException, match=match):
            getattr(client, method)(b"data") if method == "send" else client.recv()


def test_ssh_tunnel_client_close_is_best_effort():
    ws = FakeWS(close_error=ssh_tunnel.websocket.WebSocketException("boom"))

    with patch(
        "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
        return_value=ws,
    ):
        client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    client.close()

    assert ws.closed is True
