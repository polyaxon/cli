import os
import pty
import sys

from polyaxon._pty.base import BasePseudoTerminal


class SandboxPseudoTerminal(BasePseudoTerminal):
    """Bridges a raw sandbox PTY websocket to the local terminal."""

    def __init__(self, client_shell):
        super().__init__(client_shell)
        self.exit_code = 0

    def _result(self):
        return self.exit_code

    def _remote_reader(self):
        return self.client_shell.fileno()

    def _send_resize(self, cols, rows):
        self.client_shell.resize(cols, rows)

    def _send_stdin(self, data):
        self.client_shell.send_stdin(data)

    def _handle_event(self, event):
        event_type = event.get("type")
        if event_type == "exited":
            self.exit_code = int(event.get("exit_code") or 0)
            return False
        if event_type == "error":
            message = event.get("message") or event.get("error") or str(event)
            sys.stderr.write("{}\n".format(message))
            sys.stderr.flush()
            self.exit_code = 1
            return False
        return True

    def _handle_remote(self):
        frame = self.client_shell.recv()
        if isinstance(frame, bytes):
            os.write(pty.STDOUT_FILENO, frame)
            return True
        return self._handle_event(frame)
