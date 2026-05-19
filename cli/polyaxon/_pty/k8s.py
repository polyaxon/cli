import os
import pty

from clipped.utils.json import orjson_dumps
from polyaxon._client.transport import ws_client
from polyaxon._pty.base import BasePseudoTerminal


class PseudoTerminal(BasePseudoTerminal):
    """Bridges a K8s websocket exec session to the local terminal."""

    def _remote_reader(self):
        return self.client_shell.sock.sock

    def _send_resize(self, cols, rows):
        self.client_shell.write_channel(
            ws_client.RESIZE_CHANNEL, orjson_dumps({"Height": rows, "Width": cols})
        )

    def _send_stdin(self, data):
        self.client_shell.write_stdin(data)

    def _handle_remote(self):
        client_shell = self.client_shell
        if client_shell.peek_stdout():
            os.write(pty.STDOUT_FILENO, client_shell.read_stdout().encode())
        if client_shell.peek_stderr():
            os.write(pty.STDOUT_FILENO, client_shell.read_stderr().encode())
        return not client_shell.peek_channel(ws_client.ERROR_CHANNEL)
