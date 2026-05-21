import io
import threading

from polyaxon._ssh.tunnel import run_tunnel


class FakeClient:
    def __init__(self, recv_items=None, send_error=None, recv_unblock_event=None):
        self.recv_items = list(recv_items or [])
        self.send_error = send_error
        self.recv_unblock_event = recv_unblock_event
        self.sent = []
        self.close_count = 0
        self.close_event = threading.Event()
        self._lock = threading.Lock()

    def send(self, data):
        if self.send_error:
            raise self.send_error
        self.sent.append(data)

    def recv(self):
        if self.recv_unblock_event:
            self.recv_unblock_event.wait(timeout=2)
        if self.recv_items:
            item = self.recv_items.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        self.close_event.wait(timeout=2)
        return b""

    def close(self):
        with self._lock:
            self.close_count += 1
        self.close_event.set()


class BlockingStdin:
    def __init__(self, event):
        self.event = event

    def read1(self, chunk_size):
        self.event.wait(timeout=2)
        return b""


class FakeStdout:
    def __init__(self, write_error=None):
        self.buffer = io.BytesIO()
        self.flushes = 0
        self.write_error = write_error

    def write(self, data):
        if self.write_error:
            raise self.write_error
        return self.buffer.write(data)

    def flush(self):
        self.flushes += 1

    def getvalue(self):
        return self.buffer.getvalue()


def test_run_tunnel_sends_stdin_bytes_to_client():
    client = FakeClient()
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=io.BytesIO(b"input"),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert client.sent == [b"input"]
    assert stdout.getvalue() == b""
    assert stderr.getvalue() == ""


def test_run_tunnel_writes_recv_bytes_to_stdout_and_flushes():
    client = FakeClient(recv_items=[b"one", b"two", b""])
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=BlockingStdin(client.close_event),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert stdout.getvalue() == b"onetwo"
    assert stdout.flushes == 2
    assert stderr.getvalue() == ""


def test_run_tunnel_stdin_eof_closes_client_and_exits_zero():
    client = FakeClient()
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=io.BytesIO(b""),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert client.close_count == 1
    assert client.sent == []
    assert stderr.getvalue() == ""


def test_run_tunnel_websocket_eof_exits_zero():
    client = FakeClient(recv_items=[b""])
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=BlockingStdin(client.close_event),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert client.close_count == 1
    assert stderr.getvalue() == ""


def test_run_tunnel_send_error_exits_one_and_keeps_stdout_empty():
    client = FakeClient(send_error=RuntimeError("send boom"))
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=io.BytesIO(b"input"),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stdout.getvalue() == b""
    assert stderr.getvalue().count("\n") == 1
    assert "stdin send failed: send boom" in stderr.getvalue()


def test_run_tunnel_recv_error_exits_one_and_preserves_partial_stdout():
    client = FakeClient(recv_items=[b"partial", RuntimeError("recv boom")])
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=BlockingStdin(client.close_event),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stdout.getvalue() == b"partial"
    assert stderr.getvalue().count("\n") == 1
    assert "websocket recv failed: recv boom" in stderr.getvalue()


def test_run_tunnel_simultaneous_errors_write_one_stderr_line():
    client = FakeClient(
        recv_items=[RuntimeError("recv boom")],
        send_error=RuntimeError("send boom"),
    )
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=io.BytesIO(b"input"),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stderr.getvalue().count("\n") == 1


def test_run_tunnel_closes_client_once_when_both_threads_exit():
    client = FakeClient(recv_items=[b""])
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=io.BytesIO(b""),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert client.close_count == 1


def test_run_tunnel_stdin_eof_wins_over_late_websocket_bytes():
    recv_unblock_event = threading.Event()
    client = FakeClient(
        recv_items=[b"late"],
        recv_unblock_event=recv_unblock_event,
    )
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=io.BytesIO(b""),
        stdout=stdout,
        stderr=stderr,
    )
    recv_unblock_event.set()

    assert code == 0
    assert stdout.getvalue() == b""
    assert stderr.getvalue() == ""


def test_run_tunnel_stdin_os_error_is_clean_eof():
    class BrokenStdin:
        def read1(self, chunk_size):
            raise OSError("closed")

    client = FakeClient()
    stdout = FakeStdout()
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=BrokenStdin(),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert stderr.getvalue() == ""


def test_run_tunnel_stdout_write_error_exits_one():
    client = FakeClient(recv_items=[b"data"])
    stdout = FakeStdout(write_error=RuntimeError("write boom"))
    stderr = io.StringIO()

    code = run_tunnel(
        client=client,
        stdin=BlockingStdin(client.close_event),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stderr.getvalue().count("\n") == 1
    assert "stdout write failed: write boom" in stderr.getvalue()
