import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from clipped.utils.json import orjson_loads
from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._sandbox.client_utils import FsReadResult, FsWriteResult
from polyaxon._sdk.schemas import V1ExecBgStart, V1ExecBgStatus, V1RunSettings
from polyaxon._utils.test_utils import patch_settings
from polyaxon.exceptions import PolyaxonClientException


pytestmark = pytest.mark.client_mark

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


class AsyncPolyaxonClientMock:
    is_async = True

    def __init__(self):
        self.config = ClientConfigMock()
        self.runs_v1 = MagicMock()
        self.runs_v1.get_run_namespace = AsyncMock(
            return_value=V1RunSettings(namespace="lazy-ns")
        )
        self.sandbox_v1 = MagicMock()
        self.sandbox_v1.ping = AsyncMock()
        self.sandbox_v1.call_exec = AsyncMock()
        self.sandbox_v1.exec_bg = AsyncMock()
        self.sandbox_v1.get_bg_exec = AsyncMock()
        self.sandbox_v1.get_bg_exec_logs = AsyncMock()
        self.sandbox_v1.signal_bg_exec = AsyncMock()
        self.sandbox_v1.delete_bg_exec = AsyncMock()
        self.sandbox_v1.fs_mkdir = AsyncMock()
        self.sandbox_v1.create_pty = AsyncMock()

    async def aclose(self):
        pass


class SyncPolyaxonClientMock:
    is_async = False
    config = ClientConfigMock()


class AsyncResponse:
    def __init__(self, status=200, data=b"", headers=None):
        self.status = status
        self._data = data
        self.headers = headers or {}
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def read(self):
        return self._data

    def close(self):
        self.closed = True


class AsyncStreamContent:
    def __init__(self, chunks):
        self.chunks = chunks

    async def iter_chunked(self, chunk_size):
        for chunk in self.chunks:
            yield chunk


class AsyncStreamResponse:
    headers = {}

    def __init__(self, chunks=None, status=200, data=b""):
        self.status = status
        self.content = AsyncStreamContent(chunks or [])
        self._data = data
        self.closed = False

    async def read(self):
        return self._data

    def close(self):
        self.closed = True


class AsyncSession:
    def __init__(self, response):
        self.response = response
        self.get_calls = []
        self.post_calls = []
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.response

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        return self.response

    async def close(self):
        self.closed = True


class AsyncStreamSession:
    def __init__(self, response):
        self.response = response
        self.post_calls = []
        self.closed = False

    async def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        return self.response

    async def close(self):
        self.closed = True


class AsyncWSMessage:
    def __init__(self, type, data):
        self.type = type
        self.data = data


class FakeAsyncWS:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent_bytes = []
        self.sent_str = []
        self.closed = False

    async def receive(self):
        return self.messages.pop(0)

    async def send_bytes(self, data):
        self.sent_bytes.append(data)

    async def send_str(self, data):
        self.sent_str.append(data)

    async def close(self):
        self.closed = True

    def exception(self):
        return None


class AsyncWSSession:
    def __init__(self, ws):
        self.ws = ws
        self.ws_connect_calls = []
        self.closed = False

    async def ws_connect(self, url, headers=None):
        self.ws_connect_calls.append((url, headers))
        return self.ws

    async def close(self):
        self.closed = True


def make_client(sdk_client=None, namespace="ns"):
    patch_settings()
    return AsyncSandboxClient(
        owner=OWNER,
        project=PROJECT,
        run_uuid=RUN_UUID,
        namespace=namespace,
        client=sdk_client or AsyncPolyaxonClientMock(),
    )


def patch_aiohttp_session(session):
    return patch(
        "polyaxon._client.sandbox.aiohttp.ClientSession",
        MagicMock(return_value=session),
    )


def patch_async_ws_session(session):
    return patch(
        "polyaxon._client.transport.async_sandbox_ws.aiohttp.ClientSession",
        MagicMock(return_value=session),
    )


@pytest.mark.asyncio
async def test_async_sandbox_client_rejects_sync_client():
    patch_settings()

    with pytest.raises(PolyaxonClientException):
        AsyncSandboxClient(
            owner=OWNER,
            project=PROJECT,
            run_uuid=RUN_UUID,
            client=SyncPolyaxonClientMock(),
        )


@pytest.mark.asyncio
async def test_async_ping_uses_explicit_namespace():
    sdk_client = AsyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client, namespace="explicit-ns")

    await client.ping()

    sdk_client.runs_v1.get_run_namespace.assert_not_called()
    sdk_client.sandbox_v1.ping.assert_awaited_once_with(
        "explicit-ns",
        OWNER,
        PROJECT,
        RUN_UUID,
    )


@pytest.mark.asyncio
async def test_async_ping_resolves_and_caches_namespace():
    sdk_client = AsyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client, namespace=None)

    await client.ping()
    await client.ping()

    sdk_client.runs_v1.get_run_namespace.assert_awaited_once_with(
        OWNER,
        PROJECT,
        RUN_UUID,
    )
    assert sdk_client.sandbox_v1.ping.await_args_list[0].args[0] == "lazy-ns"
    assert sdk_client.sandbox_v1.ping.await_args_list[1].args[0] == "lazy-ns"


@pytest.mark.asyncio
async def test_async_process_exec_normalizes_command_env_and_stdin():
    sdk_client = AsyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client)

    await client.process.exec(
        ("echo", "hi"),
        env={"A": "B", "EMPTY": None},
        stdin=b"x",
        timeout_ms=1000,
    )

    body = sdk_client.sandbox_v1.call_exec.await_args.kwargs["body"]
    assert body.command == ["echo", "hi"]
    assert body.env == {"A": "B", "EMPTY": None}
    assert body.stdin == "eA=="
    assert body.timeout_ms == 1000


@pytest.mark.asyncio
async def test_async_logs_does_not_expose_follow_kwarg():
    client = make_client()

    with pytest.raises(TypeError):
        await client.process.logs("exec-1", follow=True)


@pytest.mark.asyncio
async def test_async_exec_stream_does_not_expose_session_kwarg():
    client = make_client()

    assert "session" not in inspect.signature(client.process.exec_stream).parameters


@pytest.mark.asyncio
async def test_async_process_exec_bg_returns_handle_and_delegates_operations():
    sdk_client = AsyncPolyaxonClientMock()
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
    client = make_client(sdk_client=sdk_client)

    handle = await client.process.exec_bg(
        ("sleep", "1"),
        env={"A": "B"},
        stdin=b"x",
        tag="nightly",
    )

    assert handle.id == "exec-1"
    assert handle.exec_id == "exec-1"
    assert handle.pid == 123
    assert handle.tag == "nightly"
    body = sdk_client.sandbox_v1.exec_bg.await_args.kwargs["body"]
    assert body.command == ["sleep", "1"]
    assert body.env == {"A": "B"}
    assert body.stdin == "eA=="
    assert body.tag == "nightly"

    assert (await handle.get()).state == "running"
    assert await handle.logs(stream="stdout", offset=5, max_bytes=10) == "logs"
    await handle.signal("SIGTERM")
    await handle.delete()

    sdk_client.sandbox_v1.get_bg_exec.assert_awaited_with(
        "ns",
        OWNER,
        PROJECT,
        RUN_UUID,
        id="exec-1",
    )
    sdk_client.sandbox_v1.get_bg_exec_logs.assert_awaited_with(
        "ns",
        OWNER,
        PROJECT,
        RUN_UUID,
        id="exec-1",
        stream="stdout",
        offset=5,
        max_bytes=10,
    )
    signal_body = sdk_client.sandbox_v1.signal_bg_exec.await_args.kwargs["body"]
    assert signal_body.signal == "SIGTERM"
    sdk_client.sandbox_v1.delete_bg_exec.assert_awaited_with(
        "ns",
        OWNER,
        PROJECT,
        RUN_UUID,
        id="exec-1",
    )


@pytest.mark.asyncio
async def test_async_process_exec_bg_wait_polls_until_terminal_status():
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.side_effect = [
        V1ExecBgStatus(exec_id="exec-1", state="running"),
        V1ExecBgStatus(exec_id="exec-1", state="exited", exit_code=0),
    ]
    client = make_client(sdk_client=sdk_client)
    handle = await client.process.exec_bg(("sleep", "1"))

    with patch(
        "polyaxon._client.sandbox.asyncio.sleep",
        new_callable=AsyncMock,
    ) as sleep:
        status = await handle.wait(timeout=10, interval=0.1)

    assert status.state == "exited"
    assert sleep.await_count == 1


@pytest.mark.asyncio
async def test_async_process_exec_bg_wait_returns_terminal_status_without_sleeping():
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
        exec_id="exec-1",
        state="exited",
        exit_code=0,
    )
    client = make_client(sdk_client=sdk_client)
    handle = await client.process.exec_bg(("true",))

    with patch(
        "polyaxon._client.sandbox.asyncio.sleep",
        new_callable=AsyncMock,
    ) as sleep:
        status = await handle.wait(timeout=10, interval=0.1)

    assert status.state == "exited"
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_async_process_exec_bg_wait_validates_timeout_and_interval():
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
        exec_id="exec-1",
        state="running",
    )
    client = make_client(sdk_client=sdk_client)
    handle = await client.process.exec_bg(("sleep", "1"))

    with pytest.raises(ValueError, match="interval"):
        await handle.wait(interval=0)
    with pytest.raises(PolyaxonClientException, match="Timed out"):
        await handle.wait(timeout=0, interval=0.1)


@pytest.mark.asyncio
async def test_async_process_exec_bg_wait_rejects_unknown_state():
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
    sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
        exec_id="exec-1",
        state="paused",
    )
    client = make_client(sdk_client=sdk_client)
    handle = await client.process.exec_bg(("sleep", "1"))

    with pytest.raises(PolyaxonClientException, match="Unknown sandbox"):
        await handle.wait(timeout=10)


@pytest.mark.asyncio
async def test_async_process_exec_bg_requires_exec_id():
    sdk_client = AsyncPolyaxonClientMock()
    sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart()
    client = make_client(sdk_client=sdk_client)

    with pytest.raises(PolyaxonClientException, match="exec_id"):
        await client.process.exec_bg(("sleep", "1"))


@pytest.mark.asyncio
async def test_async_fs_mkdir_serializes_mode_as_octal_string():
    sdk_client = AsyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client)

    await client.fs.mkdir("/tmp/data", mode=0o755)

    body = sdk_client.sandbox_v1.fs_mkdir.await_args.kwargs["body"]
    assert body.path == "/tmp/data"
    assert body.mode == "0755"


@pytest.mark.asyncio
async def test_async_pty_create_allows_default_command():
    sdk_client = AsyncPolyaxonClientMock()
    client = make_client(sdk_client=sdk_client)

    await client.pty.create()

    body = sdk_client.sandbox_v1.create_pty.await_args.kwargs["body"]
    assert body.command is None


@pytest.mark.asyncio
async def test_async_pty_attach_connects_and_uses_raw_frames():
    from polyaxon._client.transport import async_sandbox_ws

    ws = FakeAsyncWS(
        messages=[
            AsyncWSMessage(
                async_sandbox_ws.aiohttp.WSMsgType.TEXT,
                '{"type":"attached","pty_id":"pty-1","pid":123}',
            ),
            AsyncWSMessage(async_sandbox_ws.aiohttp.WSMsgType.BINARY, b"output"),
            AsyncWSMessage(
                async_sandbox_ws.aiohttp.WSMsgType.TEXT,
                '{"type":"exited","exit_code":0}',
            ),
        ]
    )
    session = AsyncWSSession(ws)
    client = make_client()

    with patch_async_ws_session(session):
        attached = await client.pty.attach("pty-1", replay_bytes=20)

    assert session.ws_connect_calls[0] == (
        "ws://polyaxon/sandbox/v1/ns/owner/project/runs/{}/pty/pty-1/ws"
        "?replay_bytes=20".format(RUN_UUID),
        {"authorization": "Bearer token"},
    )
    assert attached.attached_event == {
        "type": "attached",
        "pty_id": "pty-1",
        "pid": 123,
    }

    await attached.send_stdin(bytearray(b"echo\n"))
    await attached.send_control({"type": "resize", "cols": 100, "rows": 30})

    assert ws.sent_bytes == [b"echo\n"]
    assert orjson_loads(ws.sent_str[0].encode("utf-8")) == {
        "type": "resize",
        "cols": 100,
        "rows": 30,
    }
    assert await attached.recv() == b"output"
    assert await attached.recv() == {"type": "exited", "exit_code": 0}

    await attached.close()
    assert ws.closed is True
    assert session.closed is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message, match",
    [
        ('{"type":"error","message":"bad attach"}', "bad attach"),
        (b"not attached", "binary frame"),
        ("not json", "Invalid PTY websocket event JSON"),
        ('{"type":"ready"}', "ready"),
    ],
)
async def test_async_pty_attach_closes_and_raises_on_bad_initial_frame(
    message,
    match,
):
    from polyaxon._client.transport import async_sandbox_ws

    message_type = (
        async_sandbox_ws.aiohttp.WSMsgType.BINARY
        if isinstance(message, bytes)
        else async_sandbox_ws.aiohttp.WSMsgType.TEXT
    )
    ws = FakeAsyncWS(messages=[AsyncWSMessage(message_type, message)])
    session = AsyncWSSession(ws)
    client = make_client()

    with patch_async_ws_session(session):
        with pytest.raises(PolyaxonClientException, match=match):
            await client.pty.attach("pty-1")

    assert ws.closed is True
    assert session.closed is True


@pytest.mark.asyncio
async def test_async_process_exec_stream_sends_request_and_closes_on_context_exit():
    response = AsyncStreamResponse(
        chunks=[
            b'event: start\ndata: {"exec_id":"exec-1","pid":123}\n\n',
            b'event: stdout\ndata: {"text":"hello","offset":5}\n\n',
        ]
    )
    session = AsyncStreamSession(response)
    client = make_client()

    with patch_aiohttp_session(session):
        stream = await client.process.exec_stream(
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
    assert kwargs["headers"]["Accept"] == "text/event-stream"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["headers"]["authorization"] == "Bearer token"
    payload = orjson_loads(kwargs["data"])
    assert payload["command"] == ["echo", "hi"]
    assert payload["env"] == {"A": "B"}
    assert payload["stdin"] == "eA=="
    assert payload["timeout_ms"] == 1000

    async with stream as events:
        async for event in events:
            assert event == {"type": "start", "exec_id": "exec-1", "pid": 123}
            break

    assert response.closed is True
    assert session.closed is True


@pytest.mark.asyncio
async def test_async_process_exec_stream_rejects_invalid_command_before_session():
    client = make_client()

    with patch("polyaxon._client.sandbox.aiohttp.ClientSession") as session:
        with pytest.raises(TypeError):
            await client.process.exec_stream("echo hi")

    session.assert_not_called()


@pytest.mark.asyncio
async def test_async_process_exec_stream_error_envelope_closes_and_raises():
    response = AsyncStreamResponse(
        status=403,
        data=b'{"error":{"code":"forbidden","message":"denied"}}',
    )
    session = AsyncStreamSession(response)
    client = make_client()

    with patch_aiohttp_session(session):
        with pytest.raises(PolyaxonClientException, match="denied"):
            await client.process.exec_stream(["echo", "hi"])

    assert response.closed is True
    assert session.closed is True


@pytest.mark.asyncio
async def test_async_fs_read_parses_raw_response_headers():
    response = AsyncResponse(
        data=b"hello",
        headers={
            "X-Polyaxon-Next-Offset": "5",
            "X-Polyaxon-Eof": "true",
        },
    )
    session = AsyncSession(response)
    client = make_client()

    with patch_aiohttp_session(session):
        result = await client.fs.read("/tmp/file.txt", offset=1, length=4)

    assert result == FsReadResult(data=b"hello", next_offset=5, eof=True)
    url, kwargs = session.get_calls[0]
    assert url == (
        "http://polyaxon/sandbox/v1/ns/owner/project/runs/{}/fs/read".format(RUN_UUID)
    )
    assert kwargs["params"] == {"path": "/tmp/file.txt", "offset": 1, "length": 4}
    assert kwargs["headers"]["Accept"] == "application/octet-stream"
    assert kwargs["headers"]["authorization"] == "Bearer token"


@pytest.mark.asyncio
async def test_async_fs_write_sends_raw_bytes_and_octal_mode():
    response = AsyncResponse(
        data=b'{"path":"/tmp/file.txt","bytes_written":1,"created":true}'
    )
    session = AsyncSession(response)
    client = make_client()

    with patch_aiohttp_session(session):
        result = await client.fs.write(
            "/tmp/file.txt",
            memoryview(b"x"),
            mode=0o644,
        )

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


@pytest.mark.asyncio
async def test_async_fs_read_write_byte_and_text_helpers():
    read_response = AsyncResponse(
        data=b"hello",
        headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
    )
    read_session = AsyncSession(read_response)
    client = make_client()

    with patch_aiohttp_session(read_session):
        assert await client.fs.read_bytes("/tmp/file.txt") == b"hello"

    with patch_aiohttp_session(read_session):
        assert await client.fs.read_text("/tmp/file.txt") == "hello"

    write_response = AsyncResponse(
        data=b'{"path":"/tmp/file.txt","bytes_written":5,"created":false}'
    )
    write_session = AsyncSession(write_response)

    with patch_aiohttp_session(write_session):
        result = await client.fs.write_text("/tmp/file.txt", "hello")

    assert result == FsWriteResult(
        path="/tmp/file.txt",
        bytes_written=5,
        created=False,
    )
    assert write_session.post_calls[0][1]["data"] == b"hello"

    with pytest.raises(TypeError):
        await client.fs.write_text("/tmp/file.txt", b"not text")


@pytest.mark.asyncio
async def test_async_raw_fs_error_envelope_raises_client_exception():
    response = AsyncResponse(
        status=404,
        data=b'{"error":{"code":"not_found","message":"missing file"}}',
    )
    session = AsyncSession(response)
    client = make_client()

    with patch_aiohttp_session(session):
        with pytest.raises(PolyaxonClientException, match="missing file"):
            await client.fs.read("/tmp/missing.txt")


def test_async_client_inherits_from_sync_client():
    assert issubclass(AsyncSandboxClient, SandboxClient)
