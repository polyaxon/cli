import errno
import fcntl
import os
import pty
import select
import signal
import struct
import termios
import tty


class BasePseudoTerminal:
    """Shared local-terminal lifecycle for websocket-backed PTY sessions."""

    def __init__(self, client_shell):
        self.client_shell = client_shell

    def start(self):
        old_handler = signal.signal(signal.SIGWINCH, self._signal_winch)
        try:
            mode = tty.tcgetattr(pty.STDIN_FILENO)
            tty.setraw(pty.STDIN_FILENO)
            restore = True
        except tty.error:
            restore = False
        self._set_pty_size()
        try:
            self._loop()
        finally:
            if restore:
                tty.tcsetattr(pty.STDIN_FILENO, tty.TCSAFLUSH, mode)
            signal.signal(signal.SIGWINCH, old_handler)
            if self.client_shell:
                self.client_shell.close()
                self.client_shell = None
        return self._result()

    def _result(self):
        return None

    def _signal_winch(self, signum, frame):
        self._set_pty_size()

    def _get_pty_size(self):
        packed = fcntl.ioctl(
            pty.STDOUT_FILENO, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0)
        )
        rows, cols, _, _ = struct.unpack("HHHH", packed)
        return cols, rows

    def _set_pty_size(self):
        cols, rows = self._get_pty_size()
        self._send_resize(cols, rows)

    def _loop(self):
        while True:
            try:
                remote_reader = self._remote_reader()
                rfds, _, _ = select.select([pty.STDIN_FILENO, remote_reader], [], [])
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                raise
            if pty.STDIN_FILENO in rfds:
                data = os.read(pty.STDIN_FILENO, 1024)
                if not data:
                    break
                self._send_stdin(data)
            if remote_reader in rfds and not self._handle_remote():
                break

    def _remote_reader(self):
        raise NotImplementedError

    def _send_resize(self, cols, rows):
        raise NotImplementedError

    def _send_stdin(self, data):
        raise NotImplementedError

    def _handle_remote(self):
        raise NotImplementedError
