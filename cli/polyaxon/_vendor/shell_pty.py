# This code is based on logic from
# http://sqizit.bartletts.id.au/2011/02/14/pseudo-terminals-in-python/
# Licensed under the MIT license:
# Copyright (c) 2011 Joshua D. Bartlett
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import errno
import fcntl
import os
import pty
import select
import signal
import struct
import termios
import tty

from clipped.utils.json import orjson_dumps

from polyaxon._client.transport import ws_client


class PseudoTerminal:
    """Bridges a K8s websocket exec session to the local terminal."""

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

    def _signal_winch(self, signum, frame):
        self._set_pty_size()

    def _set_pty_size(self):
        packed = fcntl.ioctl(
            pty.STDOUT_FILENO, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0)
        )
        rows, cols, _, _ = struct.unpack("HHHH", packed)
        self.client_shell.write_channel(
            ws_client.RESIZE_CHANNEL, orjson_dumps({"Height": rows, "Width": cols})
        )

    def _loop(self):
        client_shell = self.client_shell
        while True:
            try:
                rfds, _, _ = select.select(
                    [pty.STDIN_FILENO, client_shell.sock.sock], [], []
                )
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                raise
            if pty.STDIN_FILENO in rfds:
                data = os.read(pty.STDIN_FILENO, 1024)
                if not data:
                    break
                client_shell.write_stdin(data)
            if client_shell.sock.sock in rfds:
                if client_shell.peek_stdout():
                    os.write(pty.STDOUT_FILENO, client_shell.read_stdout().encode())
                if client_shell.peek_stderr():
                    os.write(pty.STDOUT_FILENO, client_shell.read_stderr().encode())
                if client_shell.peek_channel(ws_client.ERROR_CHANNEL):
                    break
