import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._sandbox.client_utils import FsReadResult, FsWriteResult
from polyaxon._sdk.schemas import V1RunSettings
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
        self.api_client = SimpleNamespace(
            configuration=SimpleNamespace(
                verify_ssl=True,
                ssl_ca_cert=None,
                cert_file=None,
                key_file=None,
                assert_hostname=None,
                proxy=None,
                proxy_headers=None,
            )
        )
        self.runs_v1 = MagicMock()
        self.sandbox_v1 = MagicMock()

    def close(self):
        pass


class AsyncPolyaxonClientMock(SyncPolyaxonClientMock):
    is_async = True

    async def aclose(self):
        pass


class FakeResponse:
    def __init__(self, status_code=200, content=b"", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.get_calls = []
        self.post_calls = []

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
def test_streaming_and_attach_stubs_are_not_exposed():
    client = make_client()

    assert not hasattr(client.process, "exec_stream")
    assert not hasattr(client.pty, "attach")


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
