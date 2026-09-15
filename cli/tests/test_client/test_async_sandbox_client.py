import inspect
import os
from pathlib import Path
import pytest
import tempfile
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from clipped.utils.json import orjson_loads
from polyaxon._client import sandbox as sandbox_module
from polyaxon._client.sandbox import AsyncSandboxClient, SandboxClient
from polyaxon._contexts import paths as ctx_paths
from polyaxon._flow.component.component import V1Component
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.plugins import V1Plugins
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.service import V1Service
from polyaxon._k8s.namespace import DEFAULT_NAMESPACE
from polyaxon._sandbox.client_utils import (
    FsReadResult,
    FsWriteResult,
    SandboxBgOutput,
)
from polyaxon._schemas.lifecycle import V1Statuses
from polyaxon._sdk.schemas.v1_exec_bg_logs import V1ExecBgLogs
from polyaxon._sdk.schemas.v1_exec_bg_start import V1ExecBgStart
from polyaxon._sdk.schemas.v1_exec_bg_status import V1ExecBgStatus
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_run_settings import V1RunSettings
from polyaxon._utils.test_utils import BaseTestCase
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
        self.sandbox_v1.resize_pty = AsyncMock()
        self.sandbox_v1.signal_pty = AsyncMock()

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


class AsyncSequenceSession(AsyncSession):
    def __init__(self, responses):
        super().__init__(response=None)
        self.responses = list(responses)

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


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


@pytest.mark.client_mark
@pytest.mark.asyncio
class TestAsyncSandboxClient(BaseTestCase, IsolatedAsyncioTestCase):
    SET_AGENT_SETTINGS = True

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp_path = Path(directory.name)
        patcher = patch.object(
            ctx_paths,
            "CONTEXT_USER_POLYAXON_PATH",
            os.path.join(directory.name, ".polyaxon"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    def make_client(self, sdk_client=None, run_namespace="ns"):
        client = AsyncSandboxClient(
            owner=OWNER,
            project=PROJECT,
            run_uuid=RUN_UUID,
            client=sdk_client or AsyncPolyaxonClientMock(),
        )
        if run_namespace:
            client.run_data.settings = V1RunSettings(namespace=run_namespace)
        return client

    def get_created_operation(self, sdk_client):
        body = sdk_client.runs_v1.create_run.await_args.kwargs["body"]
        return V1Operation.read(body.content)

    def patch_aiohttp_session(self, session):
        return patch(
            "polyaxon._client.sandbox.aiohttp.ClientSession",
            MagicMock(return_value=session),
        )

    def patch_async_ws_session(self, session):
        return patch(
            "polyaxon._client.transport.async_sandbox_ws.aiohttp.ClientSession",
            MagicMock(return_value=session),
        )

    def test_async_sandbox_client_rejects_sync_client(self):
        with self.assertRaises(PolyaxonClientException):
            AsyncSandboxClient(
                owner=OWNER,
                project=PROJECT,
                run_uuid=RUN_UUID,
                client=SyncPolyaxonClientMock(),
            )

    def test_async_sandbox_client_does_not_expose_namespace_constructor_arg(self):
        assert "namespace" not in inspect.signature(AsyncSandboxClient).parameters

    def test_async_sandbox_client_can_initialize_without_run_uuid_for_create(self):
        with patch(
            "polyaxon._managers.run.RunConfigManager.get_config", return_value=None
        ):
            client = AsyncSandboxClient(
                owner=OWNER,
                project=PROJECT,
                client=AsyncPolyaxonClientMock(),
            )

        assert client.run_uuid is None

    async def test_async_sandbox_operations_require_run_uuid_before_create(self):
        with patch(
            "polyaxon._managers.run.RunConfigManager.get_config", return_value=None
        ):
            client = AsyncSandboxClient(
                owner=OWNER,
                project=PROJECT,
                client=AsyncPolyaxonClientMock(),
            )

        with self.assertRaisesRegex(
            PolyaxonClientException, "call `create\\(\\)` first"
        ):
            await client.ping()

    async def test_async_create_builds_default_sandbox_service_and_mutates_state(self):
        sdk_client = AsyncPolyaxonClientMock()
        created = V1Run.model_construct(
            uuid=RUN_UUID,
            settings=V1RunSettings(namespace="created-ns"),
        )
        sdk_client.runs_v1.create_run = AsyncMock(return_value=created)
        with patch(
            "polyaxon._managers.run.RunConfigManager.get_config", return_value=None
        ):
            client = AsyncSandboxClient(
                owner=OWNER,
                project=PROJECT,
                client=sdk_client,
            )

        result = await client.create(name="sandbox", tags=["debug"])

        assert result is created
        assert client.run_uuid == RUN_UUID
        assert client.run_data is created
        assert client.run_data.status == V1Statuses.CREATED
        sdk_client.runs_v1.create_run.assert_awaited_once()
        assert sdk_client.runs_v1.create_run.await_args.kwargs["owner"] == OWNER
        assert sdk_client.runs_v1.create_run.await_args.kwargs["project"] == PROJECT
        assert "async_req" not in sdk_client.runs_v1.create_run.await_args.kwargs
        body = sdk_client.runs_v1.create_run.await_args.kwargs["body"]
        assert body.name == "sandbox"
        assert body.tags == ["debug"]

        operation = self.get_created_operation(sdk_client)
        assert operation.component.run.kind == V1RunKind.SERVICE
        assert operation.component.plugins.sandbox is True
        assert client.process._parent is client
        assert client.fs._parent is client
        assert client.pty._parent is client

    async def test_async_create_merges_sandbox_plugin_into_existing_inline_content(
        self,
    ):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.runs_v1.create_run = AsyncMock(
            return_value=V1Run.model_construct(uuid=RUN_UUID)
        )
        content = V1Operation(
            component=V1Component(
                run=V1Service(),
                plugins=V1Plugins(tmux=True),
            )
        )
        with patch(
            "polyaxon._managers.run.RunConfigManager.get_config", return_value=None
        ):
            client = AsyncSandboxClient(
                owner=OWNER,
                project=PROJECT,
                client=sdk_client,
            )

        await client.create(content=content)

        operation = self.get_created_operation(sdk_client)
        assert operation.component.run.kind == V1RunKind.SERVICE
        assert operation.component.plugins.tmux is True
        assert operation.component.plugins.sandbox is True
        assert content.component.plugins.sandbox is None

    async def test_async_create_rejects_non_service_inline_content(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.runs_v1.create_run = AsyncMock()
        content = V1Operation(
            component=V1Component(
                run=V1Job(),
                plugins=V1Plugins(),
            )
        )
        with patch(
            "polyaxon._managers.run.RunConfigManager.get_config", return_value=None
        ):
            client = AsyncSandboxClient(
                owner=OWNER,
                project=PROJECT,
                client=sdk_client,
            )

        with self.assertRaisesRegex(PolyaxonClientException, "requires a service"):
            await client.create(content=content)

        sdk_client.runs_v1.create_run.assert_not_called()

    def test_async_namespace_property_uses_run_settings_or_default_namespace(self):
        client = self.make_client(run_namespace=None)

        assert client.namespace == DEFAULT_NAMESPACE

        client.run_data.settings = V1RunSettings(namespace="settings-ns")
        assert client.namespace == "settings-ns"

    async def test_async_ping_uses_namespace_from_run_settings(self):
        sdk_client = AsyncPolyaxonClientMock()
        client = self.make_client(sdk_client=sdk_client, run_namespace="settings-ns")

        await client.ping()

        sdk_client.runs_v1.get_run_namespace.assert_not_called()
        sdk_client.sandbox_v1.ping.assert_awaited_once_with(
            "settings-ns",
            OWNER,
            PROJECT,
            RUN_UUID,
        )

    async def test_async_ping_resolves_and_caches_namespace(self):
        sdk_client = AsyncPolyaxonClientMock()
        client = self.make_client(sdk_client=sdk_client, run_namespace=None)

        await client.ping()
        await client.ping()

        sdk_client.runs_v1.get_run_namespace.assert_awaited_once_with(
            OWNER,
            PROJECT,
            RUN_UUID,
        )
        assert sdk_client.sandbox_v1.ping.await_args_list[0].args[0] == "lazy-ns"
        assert sdk_client.sandbox_v1.ping.await_args_list[1].args[0] == "lazy-ns"
        assert client.run_data.settings.namespace == "lazy-ns"

    async def test_async_process_exec_normalizes_command_env_and_stdin(self):
        sdk_client = AsyncPolyaxonClientMock()
        client = self.make_client(sdk_client=sdk_client)

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

    async def test_async_logs_does_not_expose_follow_kwarg(self):
        client = self.make_client()

        with self.assertRaises(TypeError):
            await client.process.logs("exec-1", follow=True)

    def test_async_exec_stream_does_not_expose_session_kwarg(self):
        client = self.make_client()

        assert "session" not in inspect.signature(client.process.exec_stream).parameters

    async def test_async_process_exec_bg_returns_handle_and_delegates_operations(self):
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
        client = self.make_client(sdk_client=sdk_client)

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

    async def test_async_process_exec_bg_handle_exposes_log_and_kill_sugar(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec_logs.side_effect = [
            V1ExecBgLogs(data="out"),
            V1ExecBgLogs(data="err"),
            V1ExecBgLogs(data="out2"),
            V1ExecBgLogs(data="err2"),
        ]
        client = self.make_client(sdk_client=sdk_client)

        handle = await client.process.exec_bg(("sleep", "1"))

        assert await handle.stdout(offset=1, max_bytes=2) == "out"
        assert await handle.stderr() == "err"
        assert await handle.output() == SandboxBgOutput(stdout="out2", stderr="err2")
        await handle.kill("SIGKILL")

        assert sdk_client.sandbox_v1.get_bg_exec_logs.await_args_list[0].kwargs == {
            "id": "exec-1",
            "stream": "stdout",
            "offset": 1,
            "max_bytes": 2,
        }
        assert sdk_client.sandbox_v1.get_bg_exec_logs.await_args_list[1].kwargs == {
            "id": "exec-1",
            "stream": "stderr",
            "offset": 0,
            "max_bytes": None,
        }
        signal_body = sdk_client.sandbox_v1.signal_bg_exec.await_args.kwargs["body"]
        assert signal_body.signal == "SIGKILL"

    async def test_async_process_exec_bg_iter_logs_polls_offsets_until_terminal(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec_logs.side_effect = [
            V1ExecBgLogs(data="one", next_offset=3, eof=False, state="running"),
            V1ExecBgLogs(data="", next_offset=3, eof=True, state="running"),
            V1ExecBgLogs(data="two", next_offset=6, eof=True, state="exited"),
        ]
        client = self.make_client(sdk_client=sdk_client)
        handle = await client.process.exec_bg(("sleep", "1"))

        chunks = []
        with patch(
            "polyaxon._client.sandbox.asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep:
            async for chunk in handle.iter_stdout(
                max_bytes=10, timeout=10, interval=0.1
            ):
                chunks.append(chunk)

        assert chunks == ["one", "two"]
        assert sleep.await_count == 2
        assert [
            call.kwargs["offset"]
            for call in sdk_client.sandbox_v1.get_bg_exec_logs.await_args_list
        ] == [0, 3, 3]

    async def test_async_process_exec_bg_iter_logs_rejects_non_advancing_data(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec_logs.return_value = V1ExecBgLogs(
            data="x",
            next_offset=0,
            eof=False,
            state="running",
        )
        client = self.make_client(sdk_client=sdk_client)
        handle = await client.process.exec_bg(("sleep", "1"))

        with self.assertRaisesRegex(PolyaxonClientException, "did not advance"):
            async for _ in handle.iter_logs(timeout=10):
                pass

    async def test_async_process_exec_bg_iter_logs_validates_args_and_timeout(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec_logs.return_value = V1ExecBgLogs(
            data="",
            next_offset=0,
            eof=True,
            state="running",
        )
        client = self.make_client(sdk_client=sdk_client)
        handle = await client.process.exec_bg(("sleep", "1"))

        with self.assertRaisesRegex(ValueError, "offset"):
            handle.iter_logs(offset=-1)
        with self.assertRaisesRegex(ValueError, "max_bytes"):
            handle.iter_logs(max_bytes=0)
        with self.assertRaisesRegex(PolyaxonClientException, "Timed out"):
            async for _ in handle.iter_logs(timeout=0, interval=0.1):
                pass

    async def test_async_process_exec_bg_wait_polls_until_terminal_status(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec.side_effect = [
            V1ExecBgStatus(exec_id="exec-1", state="running"),
            V1ExecBgStatus(exec_id="exec-1", state="exited", exit_code=0),
        ]
        client = self.make_client(sdk_client=sdk_client)
        handle = await client.process.exec_bg(("sleep", "1"))

        with patch(
            "polyaxon._client.sandbox.asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep:
            status = await handle.wait(timeout=10, interval=0.1)

        assert status.state == "exited"
        assert sleep.await_count == 1

    async def test_async_process_exec_bg_wait_returns_terminal_status_without_sleeping(
        self,
    ):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
            exec_id="exec-1",
            state="exited",
            exit_code=0,
        )
        client = self.make_client(sdk_client=sdk_client)
        handle = await client.process.exec_bg(("true",))

        with patch(
            "polyaxon._client.sandbox.asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep:
            status = await handle.wait(timeout=10, interval=0.1)

        assert status.state == "exited"
        sleep.assert_not_awaited()

    async def test_async_process_exec_bg_wait_validates_timeout_and_interval(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
            exec_id="exec-1",
            state="running",
        )
        client = self.make_client(sdk_client=sdk_client)
        handle = await client.process.exec_bg(("sleep", "1"))

        with self.assertRaisesRegex(ValueError, "interval"):
            await handle.wait(interval=0)
        with self.assertRaisesRegex(PolyaxonClientException, "Timed out"):
            await handle.wait(timeout=0, interval=0.1)

    async def test_async_process_exec_bg_wait_rejects_unknown_state(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart(exec_id="exec-1")
        sdk_client.sandbox_v1.get_bg_exec.return_value = V1ExecBgStatus(
            exec_id="exec-1",
            state="paused",
        )
        client = self.make_client(sdk_client=sdk_client)
        handle = await client.process.exec_bg(("sleep", "1"))

        with self.assertRaisesRegex(PolyaxonClientException, "Unknown sandbox"):
            await handle.wait(timeout=10)

    async def test_async_process_exec_bg_requires_exec_id(self):
        sdk_client = AsyncPolyaxonClientMock()
        sdk_client.sandbox_v1.exec_bg.return_value = V1ExecBgStart()
        client = self.make_client(sdk_client=sdk_client)

        with self.assertRaisesRegex(PolyaxonClientException, "exec_id"):
            await client.process.exec_bg(("sleep", "1"))

    async def test_async_fs_mkdir_serializes_mode_as_octal_string(self):
        sdk_client = AsyncPolyaxonClientMock()
        client = self.make_client(sdk_client=sdk_client)

        await client.fs.mkdir("/tmp/data", mode=0o755)

        body = sdk_client.sandbox_v1.fs_mkdir.await_args.kwargs["body"]
        assert body.path == "/tmp/data"
        assert body.mode == "0755"

    async def test_async_pty_create_allows_default_command(self):
        sdk_client = AsyncPolyaxonClientMock()
        client = self.make_client(sdk_client=sdk_client)

        await client.pty.create()

        body = sdk_client.sandbox_v1.create_pty.await_args.kwargs["body"]
        assert body.command is None

    async def test_async_pty_attach_connects_and_uses_raw_frames(self):
        from polyaxon._client.transport import async_sandbox_ws

        sdk_client = AsyncPolyaxonClientMock()
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
        client = self.make_client(sdk_client=sdk_client)

        with self.patch_async_ws_session(session):
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
        await attached.resize(cols=120, rows=40)
        await attached.kill("SIGKILL")

        assert ws.sent_bytes == [b"echo\n"]
        assert orjson_loads(ws.sent_str[0].encode("utf-8")) == {
            "type": "resize",
            "cols": 100,
            "rows": 30,
        }
        assert await attached.recv() == b"output"
        assert await attached.recv() == {"type": "exited", "exit_code": 0}
        resize_body = sdk_client.sandbox_v1.resize_pty.await_args.kwargs["body"]
        assert resize_body.cols == 120
        assert resize_body.rows == 40
        signal_body = sdk_client.sandbox_v1.signal_pty.await_args.kwargs["body"]
        assert signal_body.signal == "SIGKILL"

        await attached.close()
        assert ws.closed is True
        assert session.closed is True

    async def test_async_pty_attach_closes_and_raises_on_error_frame(self):
        from polyaxon._client.transport import async_sandbox_ws

        ws = FakeAsyncWS(
            messages=[
                AsyncWSMessage(
                    async_sandbox_ws.aiohttp.WSMsgType.TEXT,
                    '{"type":"error","message":"bad attach"}',
                ),
            ]
        )
        session = AsyncWSSession(ws)
        client = self.make_client()

        with self.patch_async_ws_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "bad attach"):
                await client.pty.attach("pty-1")

        assert ws.closed is True
        assert session.closed is True

    async def test_async_pty_attach_closes_and_raises_on_binary_frame(self):
        from polyaxon._client.transport import async_sandbox_ws

        ws = FakeAsyncWS(
            messages=[
                AsyncWSMessage(
                    async_sandbox_ws.aiohttp.WSMsgType.BINARY,
                    b"not attached",
                ),
            ]
        )
        session = AsyncWSSession(ws)
        client = self.make_client()

        with self.patch_async_ws_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "binary frame"):
                await client.pty.attach("pty-1")

        assert ws.closed is True
        assert session.closed is True

    async def test_async_pty_attach_closes_and_raises_on_invalid_json(self):
        from polyaxon._client.transport import async_sandbox_ws

        ws = FakeAsyncWS(
            messages=[
                AsyncWSMessage(
                    async_sandbox_ws.aiohttp.WSMsgType.TEXT,
                    "not json",
                ),
            ]
        )
        session = AsyncWSSession(ws)
        client = self.make_client()

        with self.patch_async_ws_session(session):
            with self.assertRaisesRegex(
                PolyaxonClientException, "Invalid PTY websocket event JSON"
            ):
                await client.pty.attach("pty-1")

        assert ws.closed is True
        assert session.closed is True

    async def test_async_pty_attach_closes_and_raises_on_unexpected_event(self):
        from polyaxon._client.transport import async_sandbox_ws

        ws = FakeAsyncWS(
            messages=[
                AsyncWSMessage(
                    async_sandbox_ws.aiohttp.WSMsgType.TEXT,
                    '{"type":"ready"}',
                ),
            ]
        )
        session = AsyncWSSession(ws)
        client = self.make_client()

        with self.patch_async_ws_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "ready"):
                await client.pty.attach("pty-1")

        assert ws.closed is True
        assert session.closed is True

    async def test_async_process_exec_stream_sends_request_and_closes_on_context_exit(
        self,
    ):
        response = AsyncStreamResponse(
            chunks=[
                b'event: start\ndata: {"exec_id":"exec-1","pid":123}\n\n',
                b'event: stdout\ndata: {"text":"hello","offset":5}\n\n',
            ]
        )
        session = AsyncStreamSession(response)
        client = self.make_client()

        with self.patch_aiohttp_session(session):
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

    async def test_async_process_exec_stream_rejects_invalid_command_before_session(
        self,
    ):
        client = self.make_client()

        with patch("polyaxon._client.sandbox.aiohttp.ClientSession") as session:
            with self.assertRaises(TypeError):
                await client.process.exec_stream("echo hi")

        session.assert_not_called()

    async def test_async_process_exec_stream_error_envelope_closes_and_raises(self):
        response = AsyncStreamResponse(
            status=403,
            data=b'{"error":{"code":"forbidden","message":"denied"}}',
        )
        session = AsyncStreamSession(response)
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "denied"):
                await client.process.exec_stream(["echo", "hi"])

        assert response.closed is True
        assert session.closed is True

    async def test_async_fs_read_parses_raw_response_headers(self):
        response = AsyncResponse(
            data=b"hello",
            headers={
                "X-Polyaxon-Next-Offset": "5",
                "X-Polyaxon-Eof": "true",
            },
        )
        session = AsyncSession(response)
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            result = await client.fs.read("/tmp/file.txt", offset=1, length=4)

        assert result == FsReadResult(data=b"hello", next_offset=5, eof=True)
        url, kwargs = session.get_calls[0]
        assert url == (
            "http://polyaxon/sandbox/v1/ns/owner/project/runs/{}/fs/read".format(
                RUN_UUID
            )
        )
        assert kwargs["params"] == {"path": "/tmp/file.txt", "offset": 1, "length": 4}
        assert kwargs["headers"]["Accept"] == "application/octet-stream"
        assert kwargs["headers"]["authorization"] == "Bearer token"

    async def test_async_fs_write_sends_raw_bytes_and_octal_mode(self):
        response = AsyncResponse(
            data=b'{"path":"/tmp/file.txt","bytes_written":1,"created":true}'
        )
        session = AsyncSession(response)
        client = self.make_client()

        with self.patch_aiohttp_session(session):
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
            "http://polyaxon/sandbox/v1/ns/owner/project/runs/{}/fs/write".format(
                RUN_UUID
            )
        )
        assert kwargs["params"] == {
            "path": "/tmp/file.txt",
            "mode": "0644",
            "create": "true",
            "append": "false",
        }
        assert kwargs["data"] == b"x"
        assert kwargs["headers"]["Content-Type"] == "application/octet-stream"

    async def test_async_fs_validates_remote_paths_before_transport(self):
        sdk_client = AsyncPolyaxonClientMock()
        client = self.make_client(sdk_client=sdk_client)
        session = AsyncSession(AsyncResponse())

        with self.patch_aiohttp_session(session):
            with self.assertRaisesRegex(ValueError, "absolute"):
                await client.fs.read("tmp/file.txt")
            with self.assertRaisesRegex(ValueError, "absolute"):
                await client.fs.write("tmp/file.txt", b"x")
            with self.assertRaisesRegex(ValueError, "absolute"):
                async for _ in client.fs.iter_bytes("tmp/file.txt"):
                    pass

        assert session.get_calls == []
        assert session.post_calls == []

        with self.assertRaisesRegex(ValueError, "absolute"):
            await client.fs.ls("tmp")
        with self.assertRaisesRegex(ValueError, "absolute"):
            await client.fs.mkdir("tmp")
        with self.assertRaisesRegex(ValueError, "absolute"):
            await client.fs.rm("tmp")
        with self.assertRaisesRegex(ValueError, "absolute"):
            await client.fs.stat("tmp")

        sdk_client.sandbox_v1.fs_ls.assert_not_called()
        sdk_client.sandbox_v1.fs_mkdir.assert_not_called()
        sdk_client.sandbox_v1.fs_rm.assert_not_called()
        sdk_client.sandbox_v1.fs_stat.assert_not_called()

    async def test_async_fs_transfer_helpers_validate_remote_path_before_local_side_effects(
        self,
    ):
        client = self.make_client()

        with self.assertRaisesRegex(ValueError, "absolute"):
            await client.fs.upload_file(self.tmp_path / "missing.txt", "tmp/file.txt")

        destination = self.tmp_path / "missing-dir" / "file.txt"
        with self.assertRaisesRegex(ValueError, "absolute"):
            await client.fs.download_file("tmp/file.txt", destination)

        assert not destination.parent.exists()

    async def test_async_fs_read_write_byte_and_text_helpers(self):
        read_response = AsyncResponse(
            data=b"hello",
            headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
        )
        read_session = AsyncSession(read_response)
        client = self.make_client()

        with self.patch_aiohttp_session(read_session):
            assert await client.fs.read_bytes("/tmp/file.txt") == b"hello"

        with self.patch_aiohttp_session(read_session):
            assert await client.fs.read_text("/tmp/file.txt") == "hello"

        write_response = AsyncResponse(
            data=b'{"path":"/tmp/file.txt","bytes_written":5,"created":false}'
        )
        write_session = AsyncSession(write_response)

        with self.patch_aiohttp_session(write_session):
            result = await client.fs.write_text("/tmp/file.txt", "hello")

        assert result == FsWriteResult(
            path="/tmp/file.txt",
            bytes_written=5,
            created=False,
        )
        assert write_session.post_calls[0][1]["data"] == b"hello"

        with self.assertRaises(TypeError):
            await client.fs.write_text("/tmp/file.txt", b"not text")

    async def test_async_fs_read_bytes_pages_until_eof(self):
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b"he",
                    headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
                ),
                AsyncResponse(
                    data=b"llo",
                    headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
                ),
            ]
        )
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            assert await client.fs.read_bytes("/tmp/file.txt") == b"hello"

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

    async def test_async_fs_iter_bytes_yields_chunks(self):
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b"he",
                    headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
                ),
                AsyncResponse(
                    data=b"llo",
                    headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
                ),
            ]
        )
        client = self.make_client()
        chunks = []

        with self.patch_aiohttp_session(session):
            async for chunk in client.fs.iter_bytes("/tmp/file.txt", chunk_size=2):
                chunks.append(chunk)

        assert chunks == [b"he", b"llo"]
        assert [call[1]["params"] for call in session.get_calls] == [
            {"path": "/tmp/file.txt", "offset": 0, "length": 2},
            {"path": "/tmp/file.txt", "offset": 2, "length": 2},
        ]

    async def test_async_fs_read_bytes_honors_length_across_pages(self):
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b"ab",
                    headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
                ),
                AsyncResponse(
                    data=b"cdef",
                    headers={"X-Polyaxon-Next-Offset": "6", "X-Polyaxon-Eof": "false"},
                ),
            ]
        )
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            assert await client.fs.read_bytes("/tmp/file.txt", length=4) == b"abcd"

        assert [call[1]["params"] for call in session.get_calls] == [
            {"path": "/tmp/file.txt", "offset": 0, "length": 4},
            {"path": "/tmp/file.txt", "offset": 2, "length": 2},
        ]

    async def test_async_fs_read_text_decodes_after_paging(self):
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b"\xc3",
                    headers={"X-Polyaxon-Next-Offset": "1", "X-Polyaxon-Eof": "false"},
                ),
                AsyncResponse(
                    data=b"\xa9",
                    headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "true"},
                ),
            ]
        )
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            assert await client.fs.read_text("/tmp/file.txt") == "é"

    async def test_async_fs_read_bytes_rejects_non_advancing_response(self):
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b"x",
                    headers={"X-Polyaxon-Next-Offset": "0", "X-Polyaxon-Eof": "false"},
                ),
            ]
        )
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "did not advance"):
                await client.fs.read_bytes("/tmp/file.txt")

    async def test_async_fs_read_bytes_length_zero_does_not_request(self):
        session = AsyncSequenceSession([])
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            assert await client.fs.read_bytes("/tmp/file.txt", length=0) == b""

        assert session.get_calls == []

    async def test_async_fs_download_file_writes_chunks_and_replaces_tmp(self):
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b"he",
                    headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
                ),
                AsyncResponse(
                    data=b"llo",
                    headers={"X-Polyaxon-Next-Offset": "5", "X-Polyaxon-Eof": "true"},
                ),
            ]
        )
        client = self.make_client()
        destination = self.tmp_path / "nested" / "file.txt"

        with self.patch_aiohttp_session(session):
            result = await client.fs.download_file(
                "/tmp/file.txt",
                destination,
                chunk_size=2,
            )

        assert result == str(destination)
        assert destination.read_bytes() == b"hello"
        assert not (destination.parent / "file.txt.part").exists()

    async def test_async_fs_download_file_cleans_tmp_on_error(self):
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b"he",
                    headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
                ),
                AsyncResponse(
                    data=b"x",
                    headers={"X-Polyaxon-Next-Offset": "2", "X-Polyaxon-Eof": "false"},
                ),
            ]
        )
        client = self.make_client()
        destination = self.tmp_path / "file.txt"

        with self.patch_aiohttp_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "did not advance"):
                await client.fs.download_file(
                    "/tmp/file.txt", destination, chunk_size=2
                )

        assert not destination.exists()
        assert not (self.tmp_path / "file.txt.part").exists()

    async def test_async_fs_upload_file_writes_chunks_with_append(self):
        local_path = self.tmp_path / "local.txt"
        local_path.write_bytes(b"hello")
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b'{"path":"/tmp/file.txt","bytes_written":2,"created":true}'
                ),
                AsyncResponse(
                    data=b'{"path":"/tmp/file.txt","bytes_written":2,"created":false}'
                ),
                AsyncResponse(
                    data=b'{"path":"/tmp/file.txt","bytes_written":1,"created":false}'
                ),
            ]
        )
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            result = await client.fs.upload_file(
                local_path,
                "/tmp/file.txt",
                chunk_size=2,
                mode=0o600,
            )

        assert result == FsWriteResult(
            path="/tmp/file.txt",
            bytes_written=5,
            created=True,
        )
        assert [call[1]["data"] for call in session.post_calls] == [b"he", b"ll", b"o"]
        assert [call[1]["params"] for call in session.post_calls] == [
            {
                "path": "/tmp/file.txt",
                "mode": "0600",
                "create": "true",
                "append": "false",
            },
            {
                "path": "/tmp/file.txt",
                "mode": "0600",
                "create": "false",
                "append": "true",
            },
            {
                "path": "/tmp/file.txt",
                "mode": "0600",
                "create": "false",
                "append": "true",
            },
        ]

    async def test_async_fs_upload_file_writes_empty_file(self):
        local_path = self.tmp_path / "empty.txt"
        local_path.write_bytes(b"")
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b'{"path":"/tmp/empty.txt","bytes_written":0,"created":true}'
                ),
            ]
        )
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            result = await client.fs.upload_file(
                local_path, "/tmp/empty.txt", chunk_size=2
            )

        assert result == FsWriteResult(
            path="/tmp/empty.txt",
            bytes_written=0,
            created=True,
        )
        assert len(session.post_calls) == 1
        assert session.post_calls[0][1]["data"] == b""
        assert session.post_calls[0][1]["params"]["append"] == "false"

    async def test_async_fs_upload_file_validates_chunk_size(self):
        local_path = self.tmp_path / "local.txt"
        local_path.write_bytes(b"hello")
        client = self.make_client()

        with self.assertRaisesRegex(ValueError, "chunk_size"):
            await client.fs.upload_file(local_path, "/tmp/file.txt", chunk_size=0)

    async def test_async_fs_upload_file_stops_on_mid_upload_failure(self):
        local_path = self.tmp_path / "local.txt"
        local_path.write_bytes(b"hello!")
        session = AsyncSequenceSession(
            [
                AsyncResponse(
                    data=b'{"path":"/tmp/file.txt","bytes_written":2,"created":true}'
                ),
                AsyncResponse(
                    data=b'{"path":"/tmp/file.txt","bytes_written":2,"created":false}'
                ),
                PolyaxonClientException("write failed"),
                AsyncResponse(
                    data=b'{"path":"/tmp/file.txt","bytes_written":0,"created":false}'
                ),
            ]
        )
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "write failed"):
                await client.fs.upload_file(local_path, "/tmp/file.txt", chunk_size=2)

        assert [call[1]["data"] for call in session.post_calls] == [b"he", b"ll", b"o!"]

    async def test_async_raw_fs_error_envelope_raises_client_exception(self):
        response = AsyncResponse(
            status=404,
            data=b'{"error":{"code":"not_found","message":"missing file"}}',
        )
        session = AsyncSession(response)
        client = self.make_client()

        with self.patch_aiohttp_session(session):
            with self.assertRaisesRegex(PolyaxonClientException, "missing file"):
                await client.fs.read("/tmp/missing.txt")

    def test_async_client_inherits_from_sync_client(self):
        assert issubclass(AsyncSandboxClient, SandboxClient)
