import os
import pytest
import tempfile
from unittest.mock import patch

from polyaxon._client.transport import ssh_tunnel
from polyaxon._contexts import paths as ctx_paths
from polyaxon._utils.test_utils import BaseTestCase
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


@pytest.mark.client_mark
class TestSshTunnelTransport(BaseTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch.object(
            ctx_paths,
            "CONTEXT_USER_POLYAXON_PATH",
            os.path.join(directory.name, ".polyaxon"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    def test_ssh_tunnel_client_connects_with_headers_and_timeout(self):
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

    def test_ssh_tunnel_client_send_uses_binary_opcode(self):
        ws = FakeWS()

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

        client.send(b"SSH bytes")

        assert ws.sent == [(ssh_tunnel.OPCODE_BINARY, b"SSH bytes")]

    def test_ssh_tunnel_client_recv_returns_binary_bytes(self):
        ws = FakeWS(frames=[(ssh_tunnel.OPCODE_BINARY, b"output")])

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

        assert client.recv() == b"output"

    def test_ssh_tunnel_client_recv_returns_empty_bytes_on_close(self):
        ws = FakeWS(frames=[(ssh_tunnel.OPCODE_CLOSE, b"")])

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

        assert client.recv() == b""

    def test_ssh_tunnel_client_recv_skips_ping_and_pong(self):
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

    def test_ssh_tunnel_client_recv_rejects_text_frames(self):
        ws = FakeWS(frames=[(ssh_tunnel.OPCODE_TEXT, b"not raw ssh")])

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

        with self.assertRaisesRegex(PolyaxonClientException, "unsupported text"):
            client.recv()

    def test_ssh_tunnel_client_wraps_handshake_status_errors(self):
        error = ssh_tunnel.websocket.WebSocketBadStatusException(
            "bad status",
            401,
            resp_body=b'{"error":{"message":"unauthorized"}}',
        )

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            side_effect=error,
        ):
            with self.assertRaisesRegex(PolyaxonClientException, "unauthorized"):
                ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    def test_ssh_tunnel_client_wraps_open_errors(self):
        ws_error = ssh_tunnel.websocket.WebSocketException("boom")

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            side_effect=ws_error,
        ):
            with self.assertRaisesRegex(PolyaxonClientException, "open failed"):
                ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

    def test_ssh_tunnel_client_wraps_send_errors(self):
        ws_error = ssh_tunnel.websocket.WebSocketException("boom")
        ws = FakeWS(send_error=ws_error)

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

        with self.assertRaisesRegex(PolyaxonClientException, "send failed"):
            client.send(b"data")

    def test_ssh_tunnel_client_wraps_recv_errors(self):
        ws_error = ssh_tunnel.websocket.WebSocketException("boom")
        ws = FakeWS(recv_error=ws_error)

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

        with self.assertRaisesRegex(PolyaxonClientException, "recv failed"):
            client.recv()

    def test_ssh_tunnel_client_close_is_best_effort(self):
        ws = FakeWS(close_error=ssh_tunnel.websocket.WebSocketException("boom"))

        with patch(
            "polyaxon._client.transport.ssh_tunnel.websocket.create_connection",
            return_value=ws,
        ):
            client = ssh_tunnel.SandboxSshTunnelClient("wss://polyaxon")

        client.close()

        assert ws.closed is True
