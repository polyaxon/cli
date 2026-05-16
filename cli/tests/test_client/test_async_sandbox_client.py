import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._sandbox.client_utils import FsReadResult, FsWriteResult
from polyaxon._sdk.schemas import V1RunSettings
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
        self.sandbox_v1.get_bg_exec_logs = AsyncMock()
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

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def read(self):
        return self._data


class AsyncSession:
    def __init__(self, response):
        self.response = response
        self.get_calls = []
        self.post_calls = []

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
async def test_async_streaming_and_attach_stubs_are_not_exposed():
    client = make_client()

    assert not hasattr(client.process, "exec_stream")
    assert not hasattr(client.pty, "attach")


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
