import inspect
import pytest
from unittest.mock import MagicMock, patch

from clipped.utils.json import orjson_loads
from polyaxon._client import sandbox as sandbox_module
from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._client.transport import sandbox_ws
from polyaxon._sandbox.client_utils import (
    FsReadResult,
    FsWriteResult,
    SseFrameBuffer,
)
from polyaxon._sdk.schemas import V1ExecBgStart, V1ExecBgStatus, V1RunSettings
from polyaxon._utils.test_utils import patch_settings
from polyaxon.exceptions import PolyaxonClientException


OWNER = "owner"
PROJECT = "project"
RUN_UUID = "11111111111111111111111111111111"


class ClientConfigMock:
    host = "http://polyaxon"
    is_offline = False
    no_op = False

    def get_full_headers(self, headers=None, auth_key="Authorization"):
        value = {}
        value.update(headers or {})
        value[auth_key] = "Bearer token"
        return value


class SyncPolyaxonClientMock:
    is_async = False

    def __init__(self):
        self.config = ClientConfigMock()
        self.runs_v1 = MagicMock()
        self.sandbox_v1 = MagicMock()

    def close(self):
        pass


class AsyncPolyaxonClientMock(SyncPolyaxonClientMock):
    is_async = True

    async def aclose(self):
        pass


class FakeResponse:
    def __init__(self, status_code=200, content=b"", headers=None, chunks=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.chunks = chunks or []
        self.closed = False

    def iter_content(self, chunk_size=1):
        yield from self.chunks

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.get_calls = []
        self.post_calls = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.response

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        return self.response

    def close(self):
        self.closed = True


class FakeSequenceSession(FakeSession):
    def __init__(self, responses):
        super().__init__(response=None)
        self.responses = list(responses)

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.responses.pop(0)


class FakeSyncWS:
    def __init__(self, frames):
        self.frames = list(frames)
        self.sent = []
        self.closed = False

    def recv_data(self):
        return self.frames.pop(0)

    def send(self, data, opcode=None):
        self.sent.append((opcode, data))

    def close(self):
        self.closed = True


def make_client(sdk_client=None, namespace="ns"):
    patch_settings()
    return SandboxClient(
        owner=OWNER,
        project=PROJECT,
        run_uuid=RUN_UUID,
        namespace=namespace,
        client=sdk_client or SyncPolyaxonClientMock(),
    )


@pytest.mark.client_mark
def test_sse_frame_buffer_parses_split_frames_and_suppresses_ping():
    buffer = SseFrameBuffer()

    assert buffer.feed(b"") == []
    assert buffer.feed(b": keepalive\n\n") == []
    assert buffer.feed(b'event: stdout\ndata: {"text":"hel') == []
    assert buffer.feed(b'lo","offset":5}\n\n') == [
        {"type": "stdout", "text": "hello", "offset": 5}
    ]

    events = buffer.feed(
        b'event: ping\ndata: {}\n\nevent: execution_complete\ndata: {"exit_code":0}\n\n'
    )

    assert events == [
        {
            "type": "execution_complete",
            "exit_code": 0,
        }
    ]


@pytest.mark.client_mark
def test_sse_frame_buffer_yields_error_event():
    buffer = SseFrameBuffer()

    assert buffer.feed(b'event: error\ndata: {"message":"boom"}\n\n') == [
        {"type": "error", "message": "boom"}
    ]


@pytest.mark.client_mark
def test_sse_frame_buffer_rejects_invalid_json():
    buffer = SseFrameBuffer()

    with pytest.raises(PolyaxonClientException, match="Invalid SSE event JSON"):
        buffer.feed(b"event: stdout\ndata: nope\n\n")


@pytest.mark.client_mark
def test_sandbox_client_public_export():
    from polyaxon.client import (
        AsyncSandboxClient as ExportedAsync,
        SandboxClient as ExportedSync,
    )

    assert ExportedSync is SandboxClient
    assert ExportedAsync is AsyncSandboxClient


@pytest.mark.client_mark
def test_sandbox_client_rejects_async_client():
    patch_settings()

    with pytest.raises(PolyaxonClientException):
        SandboxClient(
            owner=OWNER,
            project=PROJECT,
            run_uuid=RUN_UUID,
            client=AsyncPolyaxonClientMock(),
        )


@pytest.mark.client_mark
def test_ping_uses_explicit_namespace():
    sdk_client = SyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client, namespace="explicit-ns")

    client.ping()

    sdk_client.runs_v1.get_run_namespace.assert_not_called()
    sdk_client.sandbox_v1.ping.assert_called_once_with(
        "explicit-ns",
        OWNER,
        PROJECT,
        RUN_UUID,
    )


@pytest.mark.client_mark
def test_ping_resolves_and_caches_namespace():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.runs_v1.get_run_namespace.return_value = V1RunSettings(
        namespace="lazy-ns"
    )
    client = make_client(sdk_client=sdk_client, namespace=None)

    client.ping()
    client.ping()

    sdk_client.runs_v1.get_run_namespace.assert_called_once_with(
        OWNER,
        PROJECT,
        RUN_UUID,
    )
    assert sdk_client.sandbox_v1.ping.call_args_list[0].args[0] == "lazy-ns"
    assert sdk_client.sandbox_v1.ping.call_args_list[1].args[0] == "lazy-ns"


@pytest.mark.client_mark
def test_namespace_resolution_raises_when_missing():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.runs_v1.get_run_namespace.return_value = V1RunSettings()
    client = make_client(sdk_client=sdk_client, namespace=None)

    with pytest.raises(PolyaxonClientException):
        client.ping()


@pytest.mark.client_mark
def test_process_exec_normalizes_command_env_and_stdin():
    sdk_client = SyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client)

    client.process.exec(
        ("echo", "hi"),
        env={"A": "B", "EMPTY": None},
        stdin=b"x",
        timeout_ms=1000,
    )

    body = sdk_client.sandbox_v1.call_exec.call_args.kwargs["body"]
    assert body.command == ["echo", "hi"]
    assert body.env == {"A": "B", "EMPTY": None}
    assert body.stdin == "eA=="
    assert body.timeout_ms == 1000


@pytest.mark.client_mark
def test_process_exec_rejects_invalid_command_and_env():
    client = make_client()

    with pytest.raises(TypeError):
        client.process.exec("echo hi")
    with pytest.raises(ValueError):
        client.process.exec([])
    with pytest.raises(TypeError):
        client.process.exec(["echo", 1])
    with pytest.raises(TypeError):
        client.process.exec(["env"], env={"A": 1})
    with pytest.raises(TypeError):
        client.process.exec(["env"], env={"A": {"nested": "bad"}})


@pytest.mark.client_mark
def test_logs_does_not_expose_follow_kwarg():
    client = make_client()

    with pytest.raises(TypeError):
        client.process.logs("exec-1", follow=True)


@pytest.mark.client_mark
def test_exec_stream_does_not_expose_session_kwarg():
    client = make_client()

    assert "session" not in inspect.signature(client.process.exec_stream).parameters


@pytest.mark.client_mark
def test_process_exec_bg_returns_handle_and_delegates_operations():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(
        exec_id="exec-1",
        pid=123,
        tag="nightly",
    )
    sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
        exec_id="exec-1",
        state="running",
    )
    sdk_client.sandbox_v1.get_bg_exec_logs.return_value = "logs"
    sdk_client.sandbox_v1.signal_bg_exec.return_value = None
    sdk_client.sandbox_v1.delete_bg_exec.return_value = None
    client = make_client(sdk_client=sdk_client)

    handle = client.process.exec_bg(
        ("sleep", "1"),
        env={"A": "B"},
        stdin=b"x",
        tag="nightly",
    )

    assert handle.id == "exec-1"
    assert handle.exec_id == "exec-1"
    assert handle.pid == 123
    assert handle.tag == "nightly"
    body = sdk_client.sandbox_v1.exec_bg.call_args.kwargs["body"]
    assert body.command == ["sleep", "1"]
    assert body.env == {"A": "B"}
    assert body.stdin == "eA=="
    assert body.tag == "nightly"

    assert handle.get().state == "running"
    assert handle.logs(stream="stdout", offset=5, max_bytes=10) == "logs"
    handle.signal("SIGTERM")
    handle.delete()

    sdk_client.sandbox_v1.get_bg_exec.assert_called_with(
        "ns",
        OWNER,
        PROJECT,
        RUN_UUID,
        id="exec-1",
    )
    sdk_client.sandbox_v1.get_bg_exec_logs.assert_called_with(
        "ns",
        OWNER,
        PROJECT,
        RUN_UUID,
        id="exec-1",
        stream="stdout",
        offset=5,
        max_bytes=10,
    )
    signal_body = sdk_client.sandbox_v1.signal_bg_exec.call_args.kwargs["body"]
    assert signal_body.signal == "SIGTERM"
    sdk_client.sandbox_v1.delete_bg_exec.assert_called_with(
        "ns",
        OWNER,
        PROJECT,
        RUN_UUID,
        id="exec-1",
    )


@pytest.mark.client_mark
def test_process_exec_bg_wait_polls_until_terminal_status():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.side_effect = [
        V1ExecBgStatus(exec_id="exec-1", state="running"),
        V1ExecBgStatus(exec_id="exec-1", state="exited", exit_code=0),
    ]
    client = make_client(sdk_client=sdk_client)
    handle = client.process.exec_bg(("sleep", "1"))

    with patch("polyaxon._client.sandbox.time.sleep") as sleep:
        status = handle.wait(timeout=10, interval=0.1)

    assert status.state == "exited"
    assert sleep.call_count == 1


@pytest.mark.client_mark
def test_bg_exec_state_sets_match_server_enum():
    assert sandbox_module._BG_RUNNING_STATES == {"running"}
    assert sandbox_module._BG_TERMINAL_STATES == {
        "exited",
        "signaled",
        "timed_out",
        "failed_to_start",
        "orphaned",
    }


@pytest.mark.client_mark
def test_process_exec_bg_wait_returns_terminal_status_without_sleeping():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
        exec_id="exec-1",
        state="exited",
        exit_code=0,
    )
    client = make_client(sdk_client=sdk_client)
    handle = client.process.exec_bg(("true",))

    with patch("polyaxon._client.sandbox.time.sleep") as sleep:
        status = handle.wait(timeout=10, interval=0.1)

    assert status.state == "exited"
    sleep.assert_not_called()


@pytest.mark.client_mark
def test_process_exec_bg_wait_validates_timeout_and_interval():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
        exec_id="exec-1",
        state="running",
    )
    client = make_client(sdk_client=sdk_client)
    handle = client.process.exec_bg(("sleep", "1"))

    with pytest.raises(ValueError, match="interval"):
        handle.wait(interval=0)
    with pytest.raises(PolyaxonClientException, match="Timed out"):
        handle.wait(timeout=0, interval=0.1)


@pytest.mark.client_mark
def test_process_exec_bg_wait_rejects_unknown_state():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
        exec_id="exec-1",
        state="paused",
    )
    client = make_client(sdk_client=sdk_client)
    handle = client.process.exec_bg(("sleep", "1"))

    with pytest.raises(PolyaxonClientException, match="Unknown sandbox"):
        handle.wait(timeout=10)


@pytest.mark.client_mark
def test_process_exec_bg_handle_does_not_delegate_unknown_attrs_to_start():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    client = make_client(sdk_client=sdk_client)
    handle = client.process.exec_bg(("sleep", "1"))

    with pytest.raises(AttributeError):
        handle.exit_code


@pytest.mark.client_mark
def test_process_exec_bg_requires_exec_id():
    sdk_client = SyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart()
    client = make_client(sdk_client=sdk_client)

    with pytest.raises(PolyaxonClientException, match="exec_id"):
        client.process.exec_bg(("sleep", "1"))


@pytest.mark.client_mark
def test_pty_attach_connects_and_uses_raw_frames():
    ws = FakeSyncWS(
        frames=[
            (
                sandbox_ws.OPCODE_TEXT,
                b'{"type":"attached","pty_id":"pty-1","pid":123}',
            ),
            (sandbox_ws.OPCODE_BINARY, b"output"),
            (sandbox_ws.OPCODE_TEXT, b'{"type":"exited","exit_code":0}'),
        ]
    )
    client = make_client()

    with patch(
        "polyaxon._client.transport.sandbox_ws.websocket.create_connection",
        return_value=ws,
    ) as connect:
        attached = client.pty.attach("pty-1", replay_bytes=20)

    assert connect.call_args.args[0] == (
        "ws://polyaxon/sandbox/v1/ns/owner/project/runs/{}/pty/pty-1/ws"
        "?replay_bytes=20".format(RUN_UUID)
    )
    assert "authorization: Bearer token" in connect.call_args.kwargs["header"]
    assert attached.attached_event == {
        "type": "attached",
        "pty_id": "pty-1",
        "pid": 123,
    }

    attached.send_stdin(b"echo\n")
    attached.send_control({"type": "resize", "cols": 100, "rows": 30})

    assert ws.sent[0] == (sandbox_ws.OPCODE_BINARY, b"echo\n")
    assert ws.sent[1][0] == sandbox_ws.OPCODE_TEXT
    assert orjson_loads(ws.sent[1][1].encode("utf-8")) == {
        "type": "resize",
        "cols": 100,
        "rows": 30,
    }
    assert attached.recv() == b"output"
    assert attached.recv() == {"type": "exited", "exit_code": 0}

    attached.close()
    assert ws.closed is True


@pytest.mark.client_mark
@pytest.mark.parametrize(
    "frame, match",
    [
        ((1, b'{"type":"error","message":"bad attach"}'), "bad attach"),
        ((2, b"not attached"), "binary frame"),
        ((1, b"not json"), "Invalid PTY websocket event JSON"),
        ((1, b'{"type":"ready"}'), "ready"),
    ],
)
def test_pty_attach_closes_and_raises_on_bad_initial_frame(frame, match):
    ws = FakeSyncWS(frames=[frame])
    client = make_client()

    with patch(
        "polyaxon._client.transport.sandbox_ws.websocket.create_connection",
        return_value=ws,
    ):
        with pytest.raises(PolyaxonClientException, match=match):
            client.pty.attach("pty-1")

    assert ws.closed is True


@pytest.mark.client_mark
def test_process_exec_stream_sends_request_and_closes_on_context_exit():
    response = FakeResponse(
        chunks=[
            b'event: start\ndata: {"exec_id":"exec-1","pid":123}\n\n',
            b'event: stdout\ndata: {"text":"hello","offset":5}\n\n',
        ]
    )
    session = FakeSession(response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        stream = client.process.exec_stream(
            ("echo", "hi"),
            env={"A": "B"},
            stdin=b"x",
            timeout_ms=1000,
        )

    url, kwargs = session.post_calls[0]
    assert url == (
        "http://polyaxon/sandbox/v1/ns/owner/project/runs/{}/exec/stream".format(
            RUN_UUID
        )
    )
    assert kwargs["stream"] is True
    assert kwargs["headers"]["Accept"] == "text/event-stream"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["headers"]["authorization"] == "Bearer token"
    payload = orjson_loads(kwargs["data"])
    assert payload["command"] == ["echo", "hi"]
    assert payload["env"] == {"A": "B"}
    assert payload["stdin"] == "eA=="
    assert payload["timeout_ms"] == 1000

    with stream as events:
        assert next(events) == {"type": "start", "exec_id": "exec-1", "pid": 123}

    assert response.closed is True
    assert session.closed is True


@pytest.mark.client_mark
def test_process_exec_stream_raises_on_4xx_with_server_error_envelope():
    response = FakeResponse(
        status_code=403,
        content=b'{"error":{"code":"forbidden","message":"denied"}}',
    )
    session = FakeSession(response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        with pytest.raises(PolyaxonClientException, match="denied"):
            client.process.exec_stream(("echo", "hi"))

    assert session.closed is True


@pytest.mark.client_mark
def test_process_exec_stream_rejects_invalid_command_before_opening_session():
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session") as session:
        with pytest.raises(TypeError):
            client.process.exec_stream("echo hi")

    session.assert_not_called()


@pytest.mark.client_mark
def test_process_exec_stream_error_envelope_closes_and_raises():
    response = FakeResponse(
        status_code=403,
        content=b'{"error":{"code":"forbidden","message":"denied"}}',
    )
    session = FakeSession(response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        with pytest.raises(PolyaxonClientException, match="denied"):
            client.process.exec_stream(["echo", "hi"])

    assert response.closed is True
    assert session.closed is True


@pytest.mark.client_mark
def test_fs_mkdir_serializes_mode_as_octal_string():
    sdk_client = SyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client)

    client.fs.mkdir("/tmp/data", mode=0o755)

    body = sdk_client.sandbox_v1.fs_mkdir.call_args.kwargs["body"]
    assert body.path == "/tmp/data"
    assert body.mode == "0755"


@pytest.mark.client_mark
def test_pty_create_allows_default_command_and_normalizes_explicit_command():
    sdk_client = SyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client)

    client.pty.create()
    assert sdk_client.sandbox_v1.create_pty.call_args.kwargs["body"].command is None

    client.pty.create(command=("sh", "-l"))
    body = sdk_client.sandbox_v1.create_pty.call_args.kwargs["body"]
    assert body.command == ["sh", "-l"]


@pytest.mark.client_mark
def test_fs_read_parses_raw_response_headers():
    response = FakeResponse(
        content=b"hello",
        headers={
            "X-Polyaxon-Next-Offset": "5",
            "X-Polyaxon-Eof": "true",
        },
    )
    session = FakeSession(response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        result = client.fs.read("/tmp/file.txt", offset=1, length=4)

    assert result == FsReadResult(data=b"hello", next_offset=5, eof=True)
    url, kwargs = session.get_calls[0]
    assert url == (
        "http://polyaxon/sandbox/v1/ns/owner/project/runs/{}/fs/read".format(RUN_UUID)
    )
    assert kwargs["params"] == {"path": "/tmp/file.txt", "offset": 1, "length": 4}
    assert kwargs["headers"]["Accept"] == "application/octet-stream"
    assert kwargs["headers"]["authorization"] == "Bearer token"


@pytest.mark.client_mark
def test_fs_write_sends_raw_bytes_and_octal_mode():
    response = FakeResponse(
        content=b'{"path":"/tmp/file.txt","bytes_written":1,"created":true}'
    )
    session = FakeSession(response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        result = client.fs.write("/tmp/file.txt", bytearray(b"x"), mode=0o644)

    assert result == FsWriteResult(
        path="/tmp/file.txt",
        bytes_written=1,
        created=True,
    )
    url, kwargs = session.post_calls[0]
    assert url == (
        "http://polyaxon/sandbox/v1/ns/owner/project/runs/{}/fs/write".format(RUN_UUID)
    )
    assert kwargs["params"] == {
        "path": "/tmp/file.txt",
        "mode": "0644",
        "create": True,
        "append": False,
    }
    assert kwargs["data"] == b"x"
    assert kwargs["headers"]["Content-Type"] == "application/octet-stream"


@pytest.mark.client_mark
def test_fs_write_accepts_memoryview_and_rejects_str():
    response = FakeResponse(
        content=b'{"path":"/tmp/file.txt","bytes_written":1,"created":true}'
    )
    session = FakeSession(response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        client.fs.write("/tmp/file.txt", memoryview(b"x"))
        with pytest.raises(TypeError):
            client.fs.write("/tmp/file.txt", "x")

    assert session.post_calls[0][1]["data"] == b"x"


@pytest.mark.client_mark
def test_fs_read_write_byte_and_text_helpers():
    read_response = FakeResponse(
        content=b"hello",
        headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
    )
    read_session = FakeSession(read_response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=read_session):
        assert client.fs.read_bytes("/tmp/file.txt") == b"hello"

    with patch("polyaxon._client.sandbox.requests.Session", return_value=read_session):
        assert client.fs.read_text("/tmp/file.txt") == "hello"

    write_response = FakeResponse(
        content=b'{"path":"/tmp/file.txt","bytes_written":5,"created":false}'
    )
    write_session = FakeSession(write_response)

    with patch(
        "polyaxon._client.sandbox.requests.Session",
        return_value=write_session,
    ):
        result = client.fs.write_text("/tmp/file.txt", "hello")

    assert result == FsWriteResult(
        path="/tmp/file.txt",
        bytes_written=5,
        created=False,
    )
    assert write_session.post_calls[0][1]["data"] == b"hello"

    with pytest.raises(TypeError):
        client.fs.write_text("/tmp/file.txt", b"not text")


@pytest.mark.client_mark
def test_fs_read_bytes_pages_until_eof():
    session = FakeSequenceSession(
        [
            FakeResponse(
                content=b"he",
                headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
            ),
            FakeResponse(
                content=b"llo",
                headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
            ),
        ]
    )
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        assert client.fs.read_bytes("/tmp/file.txt") == b"hello"

    assert [call[1]["params"] for call in session.get_calls] == [
        {
            "path": "/tmp/file.txt",
            "offset": 0,
            "length": sandbox_module._DEFAULT_FILE_CHUNK_SIZE,
        },
        {
            "path": "/tmp/file.txt",
            "offset": 2,
            "length": sandbox_module._DEFAULT_FILE_CHUNK_SIZE,
        },
    ]


@pytest.mark.client_mark
def test_fs_iter_bytes_yields_chunks():
    session = FakeSequenceSession(
        [
            FakeResponse(
                content=b"he",
                headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
            ),
            FakeResponse(
                content=b"llo",
                headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
            ),
        ]
    )
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        assert list(client.fs.iter_bytes("/tmp/file.txt", chunk_size=2)) == [
            b"he",
            b"llo",
        ]

    assert [call[1]["params"] for call in session.get_calls] == [
        {"path": "/tmp/file.txt", "offset": 0, "length": 2},
        {"path": "/tmp/file.txt", "offset": 2, "length": 2},
    ]


@pytest.mark.client_mark
def test_fs_read_bytes_honors_length_across_pages():
    session = FakeSequenceSession(
        [
            FakeResponse(
                content=b"ab",
                headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
            ),
            FakeResponse(
                content=b"cdef",
                headers={"X-Polyaxon-Next-Offset": "6", "X-Polyaxon-Eof": "false"},
            ),
        ]
    )
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        assert client.fs.read_bytes("/tmp/file.txt", length=4) == b"abcd"

    assert [call[1]["params"] for call in session.get_calls] == [
        {"path": "/tmp/file.txt", "offset": 0, "length": 4},
        {"path": "/tmp/file.txt", "offset": 2, "length": 2},
    ]


@pytest.mark.client_mark
def test_fs_read_text_decodes_after_paging():
    session = FakeSequenceSession(
        [
            FakeResponse(
                content=b"\xc3",
                headers={"X-Polyaxon-Next-Offset": "1", "X-Polyaxon-Eof": "false"},
            ),
            FakeResponse(
                content=b"\xa9",
                headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "true"},
            ),
        ]
    )
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        assert client.fs.read_text("/tmp/file.txt") == "é"


@pytest.mark.client_mark
def test_fs_read_bytes_rejects_non_advancing_response():
    session = FakeSequenceSession(
        [
            FakeResponse(
                content=b"x",
                headers={"X-Polyaxon-Next-Offset": "0", "X-Polyaxon-Eof": "false"},
            ),
        ]
    )
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        with pytest.raises(PolyaxonClientException, match="did not advance"):
            client.fs.read_bytes("/tmp/file.txt")


@pytest.mark.client_mark
def test_fs_read_bytes_length_zero_does_not_request():
    session = FakeSequenceSession([])
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        assert client.fs.read_bytes("/tmp/file.txt", length=0) == b""

    assert session.get_calls == []


@pytest.mark.client_mark
def test_fs_download_file_writes_chunks_and_replaces_tmp(tmp_path):
    session = FakeSequenceSession(
        [
            FakeResponse(
                content=b"he",
                headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
            ),
            FakeResponse(
                content=b"llo",
                headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
            ),
        ]
    )
    client = make_client()
    destination = tmp_path / "nested" / "file.txt"

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        result = client.fs.download_file(
            "/tmp/file.txt",
            destination,
            chunk_size=2,
        )

    assert result == str(destination)
    assert destination.read_bytes() == b"hello"
    assert not (destination.parent / "file.txt.part").exists()


@pytest.mark.client_mark
def test_fs_download_file_cleans_tmp_on_error(tmp_path):
    session = FakeSequenceSession(
        [
            FakeResponse(
                content=b"he",
                headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
            ),
            FakeResponse(
                content=b"x",
                headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
            ),
        ]
    )
    client = make_client()
    destination = tmp_path / "file.txt"

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        with pytest.raises(PolyaxonClientException, match="did not advance"):
            client.fs.download_file("/tmp/file.txt", destination, chunk_size=2)

    assert not destination.exists()
    assert not (tmp_path / "file.txt.part").exists()


@pytest.mark.client_mark
def test_raw_fs_error_envelope_raises_client_exception():
    response = FakeResponse(
        status_code=404,
        content=b'{"error":{"code":"not_found","message":"missing file"}}',
    )
    session = FakeSession(response)
    client = make_client()

    with patch("polyaxon._client.sandbox.requests.Session", return_value=session):
        with pytest.raises(PolyaxonClientException, match="missing file"):
            client.fs.read("/tmp/missing.txt")
