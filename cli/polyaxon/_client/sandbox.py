import asyncio
import inspect
import os
from pathlib import Path
import requests
import time
from typing import Optional
from urllib.parse import urlencode

import aiohttp

from clipped.utils.bools import to_bool
from clipped.utils.encoding import BytesLike, as_bytes, b64_data
from clipped.utils.http import absolute_uri, to_ws_url
from clipped.utils.json import orjson_dumps, orjson_loads
from polyaxon import settings
from polyaxon._client.client import PolyaxonClient
from polyaxon._client.decorators import (
    async_client_handler,
    client_handler,
    get_global_or_inline_config,
)
from polyaxon._client.mixin import ClientMixin
from polyaxon._client.transport import async_sandbox_ws, sandbox_ws
from polyaxon._env_vars.getters import (
    get_project_error_message,
    get_project_or_local,
    get_run_or_local,
)
from polyaxon._sandbox.client_utils import (
    FsReadResult,
    FsWriteResult,
    SandboxBgOutput,
    SseFrameBuffer,
    format_mode,
    format_query_bool,
    normalize_command,
    normalize_env,
    parse_error_message,
    validate_remote_path,
)
from polyaxon._sdk.schemas import (
    V1CreatePtyRequest,
    V1ExecBgRequest,
    V1ExecRequest,
    V1FsMkdirRequest,
    V1ResizePtyRequest,
    V1SignalRequest,
)
from polyaxon._utils.fqn_utils import get_entity_full_name, split_owner_team_space
from polyaxon._utils.urls_utils import get_proxy_run_url
from polyaxon.api import SANDBOX_V1_LOCATION
from polyaxon.exceptions import PolyaxonClientException


_DEFAULT_FILE_CHUNK_SIZE = 64 * 1024


class SandboxClient(ClientMixin):
    @client_handler(check_no_op=True)
    def __init__(
        self,
        owner: Optional[str] = None,
        project: Optional[str] = None,
        run_uuid: Optional[str] = None,
        namespace: Optional[str] = None,
        client: Optional[PolyaxonClient] = None,
        is_offline: Optional[bool] = None,
        no_op: Optional[bool] = None,
        manual_exceptions_handling: bool = False,
    ):
        self._manual_exceptions_handling = manual_exceptions_handling
        self._is_offline = get_global_or_inline_config(
            config_key="is_offline",
            config_value=is_offline,
            client=client,
        )
        self._no_op = get_global_or_inline_config(
            config_key="no_op",
            config_value=no_op,
            client=client,
        )

        if self._no_op:
            return

        try:
            owner, _, project = get_project_or_local(
                get_entity_full_name(owner=owner, entity=project)
            )
        except PolyaxonClientException:
            pass

        error_message = get_project_error_message(owner, project)
        if error_message:
            raise PolyaxonClientException(error_message)

        run_uuid = get_run_or_local(run_uuid)
        if not run_uuid:
            raise PolyaxonClientException("Please provide a valid run uuid.")

        owner, team = split_owner_team_space(owner)
        self._set_client(client)
        self._owner = owner
        self._team = team
        self._project = project
        self._run_uuid = run_uuid
        self._namespace = namespace
        self._set_subclients()

    def _set_subclients(self):
        self.process = _ProcessSubClient(self)
        self.fs = _FsSubClient(self)
        self.pty = _PtySubClient(self)

    @property
    def run_uuid(self) -> str:
        return self._run_uuid

    @property
    def namespace(self) -> Optional[str]:
        return self._namespace

    def _get_namespace(self) -> str:
        if self._namespace:
            return self._namespace

        settings_ = self.client.runs_v1.get_run_namespace(
            self.owner,
            self.project,
            self.run_uuid,
        )
        namespace = getattr(settings_, "namespace", None)
        if not namespace:
            raise PolyaxonClientException(
                "Could not resolve sandbox run namespace for run `{}`.".format(
                    self.run_uuid
                )
            )
        self._namespace = namespace
        return namespace

    def _sandbox_url(self, namespace: str, subpath: str) -> str:
        url = get_proxy_run_url(
            service=SANDBOX_V1_LOCATION,
            namespace=namespace,
            owner=self.owner,
            project=self.project,
            run_uuid=self.run_uuid,
            subpath=subpath,
        )
        return absolute_uri(url=url, host=self.client.config.host)

    @client_handler(check_no_op=True)
    def ping(self):
        return self.client.sandbox_v1.ping(
            self._get_namespace(),
            self.owner,
            self.project,
            self.run_uuid,
        )


class AsyncSandboxClient(SandboxClient):
    _IS_ASYNC = True

    def _set_subclients(self):
        self.process = _AsyncProcessSubClient(self)
        self.fs = _AsyncFsSubClient(self)
        self.pty = _AsyncPtySubClient(self)

    async def _get_namespace(self) -> str:
        if self._namespace:
            return self._namespace

        settings_ = await self.client.runs_v1.get_run_namespace(
            self.owner,
            self.project,
            self.run_uuid,
        )
        namespace = getattr(settings_, "namespace", None)
        if not namespace:
            raise PolyaxonClientException(
                "Could not resolve sandbox run namespace for run `{}`.".format(
                    self.run_uuid
                )
            )
        self._namespace = namespace
        return namespace

    @async_client_handler(check_no_op=True)
    async def ping(self):
        return await self.client.sandbox_v1.ping(
            await self._get_namespace(),
            self.owner,
            self.project,
            self.run_uuid,
        )


class _BaseSubClient:
    def __init__(self, parent: SandboxClient):
        self._parent = parent

    @property
    def _manual_exceptions_handling(self):
        return getattr(self._parent, "_manual_exceptions_handling", False)

    @property
    def _no_op(self):
        return getattr(self._parent, "_no_op", None)

    @property
    def _is_offline(self):
        return getattr(self._parent, "_is_offline", None)

    @property
    def _client(self):
        return getattr(self._parent, "_client", None)

    def _run_args(self):
        return (
            self._parent._get_namespace(),
            self._parent.owner,
            self._parent.project,
            self._parent.run_uuid,
        )

    def _url(self, subpath: str) -> str:
        return self._parent._sandbox_url(self._parent._get_namespace(), subpath)

    def _headers(self, headers=None):
        return self._parent.client.config.get_full_headers(
            headers=headers,
            auth_key="authorization",
        )

    def _request_kwargs(self, headers=None, timeout=None):
        return {
            "headers": self._headers(headers=headers),
            "timeout": timeout or settings.LONG_REQUEST_TIMEOUT,
        }

    @staticmethod
    def _raise_for_response(response, action: str):
        if response.status_code < 400:
            return
        fallback = "{} failed with status {}".format(action, response.status_code)
        # Safe for stream=True responses: this branch only runs on error envelopes.
        raise PolyaxonClientException(parse_error_message(response.content, fallback))


class _AsyncBaseSubClient(_BaseSubClient):
    async def _run_args(self):
        return (
            await self._parent._get_namespace(),
            self._parent.owner,
            self._parent.project,
            self._parent.run_uuid,
        )

    async def _url(self, subpath: str) -> str:
        return self._parent._sandbox_url(await self._parent._get_namespace(), subpath)

    def _client_timeout(self, timeout=None):
        if isinstance(timeout, aiohttp.ClientTimeout):
            return timeout
        return aiohttp.ClientTimeout(total=timeout or settings.LONG_REQUEST_TIMEOUT)

    def _session_kwargs(self, timeout=None):
        return {
            "timeout": self._client_timeout(timeout),
            "trust_env": True,
        }

    def _request_kwargs(self, headers=None):
        return {"headers": self._headers(headers=headers)}

    @staticmethod
    async def _raise_for_response(response, data: bytes, action: str):
        if response.status < 400:
            return
        fallback = "{} failed with status {}".format(action, response.status)
        raise PolyaxonClientException(parse_error_message(data, fallback))


def _attached_error_message(event):
    return event.get("message") or event.get("error") or "PTY attach failed."


def _validate_attached_message(message):
    if isinstance(message, bytes):
        raise PolyaxonClientException(
            "Expected PTY attached control event, received binary frame."
        )
    event_type = message.get("type")
    if event_type == "attached":
        return message
    if event_type == "error":
        raise PolyaxonClientException(_attached_error_message(message))
    raise PolyaxonClientException(
        "Expected PTY attached control event, received `{}`.".format(
            event_type or "unknown"
        )
    )


_BG_RUNNING_STATES = {"running"}
_BG_TERMINAL_STATES = {
    "exited",
    "signaled",
    "timed_out",
    "failed_to_start",
    "orphaned",
}


def _is_bg_exec_terminal(status) -> bool:
    state = getattr(status, "state", None)
    if not state:
        return False
    state = str(state).lower()
    if state in _BG_TERMINAL_STATES:
        return True
    if state in _BG_RUNNING_STATES:
        return False
    raise PolyaxonClientException(
        "Unknown sandbox background exec state `{}`.".format(state)
    )


def _validate_wait_args(timeout, interval):
    if timeout is not None and timeout < 0:
        raise ValueError("timeout must be greater than or equal to 0")
    if interval <= 0:
        raise ValueError("interval must be greater than 0")


def _validate_log_iter_args(offset: int, max_bytes, timeout, interval):
    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0")
    if max_bytes is not None and max_bytes <= 0:
        raise ValueError("max_bytes must be greater than 0")
    _validate_wait_args(timeout=timeout, interval=interval)


def _validate_fs_read_args(offset: int, length: Optional[int], chunk_size: int):
    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0")
    if length is not None and length < 0:
        raise ValueError("length must be greater than or equal to 0")
    _validate_file_chunk_size(chunk_size)


def _validate_file_chunk_size(chunk_size: int):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")


def _next_read_length(remaining: Optional[int], chunk_size: int) -> int:
    if remaining is None:
        return chunk_size
    return min(remaining, chunk_size)


def _validate_fs_read_advanced(path: str, next_offset: int, result: FsReadResult):
    if result.next_offset <= next_offset:
        raise PolyaxonClientException(
            "fs.read did not advance while reading `{}`.".format(path)
        )


def _log_data(logs) -> str:
    if isinstance(logs, str):
        return logs
    return getattr(logs, "data", None) or ""


def _log_next_offset(logs) -> int:
    next_offset = getattr(logs, "next_offset", None)
    if next_offset is None:
        raise PolyaxonClientException(
            "Sandbox background exec log response did not include next_offset."
        )
    return next_offset


def _log_is_done(logs) -> bool:
    if not getattr(logs, "eof", False):
        return False
    if getattr(logs, "state", None) is None:
        raise PolyaxonClientException(
            "Sandbox background exec log response did not include state."
        )
    return _is_bg_exec_terminal(logs)


class SandboxBgExec:
    def __init__(self, process, start):
        self._process = process
        self.start = start
        self.exec_id = getattr(start, "exec_id", None)
        if not self.exec_id:
            raise PolyaxonClientException(
                "Sandbox background exec response did not include an exec_id."
            )

    @property
    def id(self):
        return self.exec_id

    @property
    def pid(self):
        return getattr(self.start, "pid", None)

    @property
    def started_at(self):
        return getattr(self.start, "started_at", None)

    @property
    def tag(self):
        return getattr(self.start, "tag", None)

    def get(self):
        return self._process.get(self.exec_id)

    def logs(
        self,
        stream: Optional[str] = None,
        offset: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ):
        return self._process.logs(
            self.exec_id,
            stream=stream,
            offset=offset,
            max_bytes=max_bytes,
        )

    def signal(self, signal: str):
        return self._process.signal(self.exec_id, signal)

    def kill(self, signal: str = "SIGTERM"):
        return self.signal(signal)

    def delete(self):
        return self._process.delete(self.exec_id)

    def stdout(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> str:
        return _log_data(self.logs(stream="stdout", offset=offset, max_bytes=max_bytes))

    def stderr(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> str:
        return _log_data(self.logs(stream="stderr", offset=offset, max_bytes=max_bytes))

    def output(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> SandboxBgOutput:
        return SandboxBgOutput(
            stdout=self.stdout(offset=offset, max_bytes=max_bytes),
            stderr=self.stderr(offset=offset, max_bytes=max_bytes),
        )

    def iter_logs(
        self,
        stream: str = "stdout",
        offset: int = 0,
        max_bytes: Optional[int] = None,
        timeout=None,
        interval: float = 1.0,
    ):
        _validate_log_iter_args(
            offset=offset,
            max_bytes=max_bytes,
            timeout=timeout,
            interval=interval,
        )

        def _iterator():
            cursor = offset
            started_at = time.monotonic()
            while True:
                logs = self.logs(stream=stream, offset=cursor, max_bytes=max_bytes)
                data = _log_data(logs)
                next_offset = _log_next_offset(logs)
                if data and next_offset <= cursor:
                    raise PolyaxonClientException(
                        "bg exec logs did not advance for `{}`.".format(self.exec_id)
                    )
                if next_offset < cursor:
                    raise PolyaxonClientException(
                        "bg exec logs moved backwards for `{}`.".format(self.exec_id)
                    )

                cursor = next_offset
                if data:
                    yield data

                if _log_is_done(logs):
                    break
                if timeout is not None and time.monotonic() - started_at >= timeout:
                    raise PolyaxonClientException(
                        "Timed out waiting for sandbox background exec logs `{}`.".format(
                            self.exec_id
                        )
                    )
                time.sleep(interval)

        return _iterator()

    def iter_stdout(self, **kwargs):
        return self.iter_logs(stream="stdout", **kwargs)

    def iter_stderr(self, **kwargs):
        return self.iter_logs(stream="stderr", **kwargs)

    def wait(self, timeout=None, interval: float = 1.0):
        _validate_wait_args(timeout=timeout, interval=interval)
        started_at = time.monotonic()
        while True:
            status = self.get()
            if _is_bg_exec_terminal(status):
                return status
            if timeout is not None and time.monotonic() - started_at >= timeout:
                raise PolyaxonClientException(
                    "Timed out waiting for sandbox background exec `{}`.".format(
                        self.exec_id
                    )
                )
            time.sleep(interval)


class AsyncSandboxBgExec(SandboxBgExec):
    async def get(self):
        return await self._process.get(self.exec_id)

    async def logs(
        self,
        stream: Optional[str] = None,
        offset: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ):
        return await self._process.logs(
            self.exec_id,
            stream=stream,
            offset=offset,
            max_bytes=max_bytes,
        )

    async def signal(self, signal: str):
        return await self._process.signal(self.exec_id, signal)

    async def kill(self, signal: str = "SIGTERM"):
        return await self.signal(signal)

    async def delete(self):
        return await self._process.delete(self.exec_id)

    async def stdout(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> str:
        return _log_data(
            await self.logs(stream="stdout", offset=offset, max_bytes=max_bytes)
        )

    async def stderr(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> str:
        return _log_data(
            await self.logs(stream="stderr", offset=offset, max_bytes=max_bytes)
        )

    async def output(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> SandboxBgOutput:
        return SandboxBgOutput(
            stdout=await self.stdout(offset=offset, max_bytes=max_bytes),
            stderr=await self.stderr(offset=offset, max_bytes=max_bytes),
        )

    def iter_logs(
        self,
        stream: str = "stdout",
        offset: int = 0,
        max_bytes: Optional[int] = None,
        timeout=None,
        interval: float = 1.0,
    ):
        _validate_log_iter_args(
            offset=offset,
            max_bytes=max_bytes,
            timeout=timeout,
            interval=interval,
        )

        async def _iterator():
            cursor = offset
            started_at = time.monotonic()
            while True:
                logs = await self.logs(
                    stream=stream, offset=cursor, max_bytes=max_bytes
                )
                data = _log_data(logs)
                next_offset = _log_next_offset(logs)
                if data and next_offset <= cursor:
                    raise PolyaxonClientException(
                        "bg exec logs did not advance for `{}`.".format(self.exec_id)
                    )
                if next_offset < cursor:
                    raise PolyaxonClientException(
                        "bg exec logs moved backwards for `{}`.".format(self.exec_id)
                    )

                cursor = next_offset
                if data:
                    yield data

                if _log_is_done(logs):
                    break
                if timeout is not None and time.monotonic() - started_at >= timeout:
                    raise PolyaxonClientException(
                        "Timed out waiting for sandbox background exec logs `{}`.".format(
                            self.exec_id
                        )
                    )
                await asyncio.sleep(interval)

        return _iterator()

    def iter_stdout(self, **kwargs):
        return self.iter_logs(stream="stdout", **kwargs)

    def iter_stderr(self, **kwargs):
        return self.iter_logs(stream="stderr", **kwargs)

    async def wait(self, timeout=None, interval: float = 1.0):
        # Do not delegate to SandboxBgExec.wait; the sync parent uses time.sleep.
        _validate_wait_args(timeout=timeout, interval=interval)
        started_at = time.monotonic()
        while True:
            status = await self.get()
            if _is_bg_exec_terminal(status):
                return status
            if timeout is not None and time.monotonic() - started_at >= timeout:
                raise PolyaxonClientException(
                    "Timed out waiting for sandbox background exec `{}`.".format(
                        self.exec_id
                    )
                )
            await asyncio.sleep(interval)


class _SseIterator:
    def __init__(self, response, session):
        self._response = response
        self._session = session
        self._buffer = SseFrameBuffer()
        self._chunks = response.iter_content(chunk_size=8192)
        self._events = []
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        while not self._events:
            try:
                chunk = next(self._chunks)
            except StopIteration:
                self.close()
                raise
            except requests.RequestException as e:
                self.close()
                raise PolyaxonClientException(
                    "process.exec_stream failed: {}".format(e)
                ) from e

            if chunk:
                self._events.extend(self._buffer.feed(chunk))

        return self._events.pop(0)

    def close(self):
        if self._closed:
            return
        close_response = getattr(self._response, "close", None)
        if close_response:
            close_response()
        close_session = getattr(self._session, "close", None)
        if close_session:
            close_session()
        self._closed = True


class _AsyncSseIterator:
    def __init__(self, response, session):
        self._response = response
        self._session = session
        self._buffer = SseFrameBuffer()
        self._chunks = response.content.iter_chunked(8192).__aiter__()
        self._events = []
        self._closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.aclose()

    def __aiter__(self):
        return self

    async def __anext__(self):
        while not self._events:
            try:
                chunk = await self._chunks.__anext__()
            except StopAsyncIteration:
                await self.aclose()
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                await self.aclose()
                raise PolyaxonClientException(
                    "process.exec_stream failed: {}".format(e)
                ) from e

            if chunk:
                self._events.extend(self._buffer.feed(chunk))

        return self._events.pop(0)

    async def aclose(self):
        if self._closed:
            return
        close_response = getattr(self._response, "close", None)
        if close_response:
            close_response()
        close_session = getattr(self._session, "close", None)
        if close_session:
            result = close_session()
            if inspect.isawaitable(result):
                await result
        self._closed = True


class _ProcessSubClient(_BaseSubClient):
    @client_handler(check_no_op=True)
    def exec(
        self,
        command,
        env=None,
        workdir: Optional[str] = None,
        stdin: Optional[BytesLike] = None,
        timeout_ms: Optional[int] = None,
    ):
        return self._parent.client.sandbox_v1.call_exec(
            *self._run_args(),
            body=V1ExecRequest(
                command=normalize_command(command),
                env=normalize_env(env),
                workdir=workdir,
                stdin=b64_data(stdin),
                timeout_ms=timeout_ms,
            ),
        )

    @client_handler(check_no_op=True)
    def exec_stream(
        self,
        command,
        env=None,
        workdir: Optional[str] = None,
        stdin: Optional[BytesLike] = None,
        timeout_ms: Optional[int] = None,
        timeout=None,
    ):
        body = V1ExecRequest(
            command=normalize_command(command),
            env=normalize_env(env),
            workdir=workdir,
            stdin=b64_data(stdin),
            timeout_ms=timeout_ms,
        )
        session = requests.Session()
        response = None
        try:
            response = session.post(
                self._url("exec/stream"),
                data=orjson_dumps(body.to_dict()),
                stream=True,
                **self._request_kwargs(
                    headers={
                        "Accept": "text/event-stream",
                        "Content-Type": "application/json",
                    },
                    timeout=timeout,
                ),
            )
            self._raise_for_response(response, "process.exec_stream")
        except requests.RequestException as e:
            session.close()
            raise PolyaxonClientException(
                "process.exec_stream failed: {}".format(e)
            ) from e
        except Exception:
            if response is not None:
                close_response = getattr(response, "close", None)
                if close_response:
                    close_response()
            session.close()
            raise

        return _SseIterator(response=response, session=session)

    @client_handler(check_no_op=True)
    def exec_bg(
        self,
        command,
        env=None,
        workdir: Optional[str] = None,
        stdin: Optional[BytesLike] = None,
        timeout_ms: Optional[int] = None,
        tag: Optional[str] = None,
    ):
        start = self._parent.client.sandbox_v1.exec_bg(
            *self._run_args(),
            body=V1ExecBgRequest(
                command=normalize_command(command),
                env=normalize_env(env),
                workdir=workdir,
                stdin=b64_data(stdin),
                timeout_ms=timeout_ms,
                tag=tag,
            ),
        )
        return SandboxBgExec(process=self, start=start)

    @client_handler(check_no_op=True)
    def list(self, tag: Optional[str] = None):
        return self._parent.client.sandbox_v1.list_bg_execs(
            *self._run_args(),
            tag=tag,
        )

    @client_handler(check_no_op=True)
    def get(self, id: str):
        return self._parent.client.sandbox_v1.get_bg_exec(*self._run_args(), id=id)

    @client_handler(check_no_op=True)
    def logs(
        self,
        id: str,
        stream: Optional[str] = None,
        offset: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ):
        return self._parent.client.sandbox_v1.get_bg_exec_logs(
            *self._run_args(),
            id=id,
            stream=stream,
            offset=offset,
            max_bytes=max_bytes,
        )

    @client_handler(check_no_op=True)
    def signal(self, id: str, signal: str):
        return self._parent.client.sandbox_v1.signal_bg_exec(
            *self._run_args(),
            id=id,
            body=V1SignalRequest(signal=signal),
        )

    @client_handler(check_no_op=True)
    def delete(self, id: str):
        return self._parent.client.sandbox_v1.delete_bg_exec(
            *self._run_args(),
            id=id,
        )


class _AsyncProcessSubClient(_ProcessSubClient, _AsyncBaseSubClient):
    @async_client_handler(check_no_op=True)
    async def exec(
        self,
        command,
        env=None,
        workdir: Optional[str] = None,
        stdin: Optional[BytesLike] = None,
        timeout_ms: Optional[int] = None,
    ):
        return await self._parent.client.sandbox_v1.call_exec(
            *(await self._run_args()),
            body=V1ExecRequest(
                command=normalize_command(command),
                env=normalize_env(env),
                workdir=workdir,
                stdin=b64_data(stdin),
                timeout_ms=timeout_ms,
            ),
        )

    @async_client_handler(check_no_op=True)
    async def exec_stream(
        self,
        command,
        env=None,
        workdir: Optional[str] = None,
        stdin: Optional[BytesLike] = None,
        timeout_ms: Optional[int] = None,
        timeout=None,
    ):
        body = V1ExecRequest(
            command=normalize_command(command),
            env=normalize_env(env),
            workdir=workdir,
            stdin=b64_data(stdin),
            timeout_ms=timeout_ms,
        )
        session = aiohttp.ClientSession(**self._session_kwargs(timeout=timeout))
        response = None
        try:
            response = await session.post(
                await self._url("exec/stream"),
                data=orjson_dumps(body.to_dict()),
                **self._request_kwargs(
                    headers={
                        "Accept": "text/event-stream",
                        "Content-Type": "application/json",
                    }
                ),
            )
            if response.status >= 400:
                data = await response.read()
                await self._raise_for_response(response, data, "process.exec_stream")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            await session.close()
            raise PolyaxonClientException(
                "process.exec_stream failed: {}".format(e)
            ) from e
        except Exception:
            if response is not None:
                close_response = getattr(response, "close", None)
                if close_response:
                    close_response()
            await session.close()
            raise

        return _AsyncSseIterator(response=response, session=session)

    @async_client_handler(check_no_op=True)
    async def exec_bg(
        self,
        command,
        env=None,
        workdir: Optional[str] = None,
        stdin: Optional[BytesLike] = None,
        timeout_ms: Optional[int] = None,
        tag: Optional[str] = None,
    ):
        start = await self._parent.client.sandbox_v1.exec_bg(
            *(await self._run_args()),
            body=V1ExecBgRequest(
                command=normalize_command(command),
                env=normalize_env(env),
                workdir=workdir,
                stdin=b64_data(stdin),
                timeout_ms=timeout_ms,
                tag=tag,
            ),
        )
        return AsyncSandboxBgExec(process=self, start=start)

    @async_client_handler(check_no_op=True)
    async def list(self, tag: Optional[str] = None):
        return await self._parent.client.sandbox_v1.list_bg_execs(
            *(await self._run_args()),
            tag=tag,
        )

    @async_client_handler(check_no_op=True)
    async def get(self, id: str):
        return await self._parent.client.sandbox_v1.get_bg_exec(
            *(await self._run_args()),
            id=id,
        )

    @async_client_handler(check_no_op=True)
    async def logs(
        self,
        id: str,
        stream: Optional[str] = None,
        offset: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ):
        return await self._parent.client.sandbox_v1.get_bg_exec_logs(
            *(await self._run_args()),
            id=id,
            stream=stream,
            offset=offset,
            max_bytes=max_bytes,
        )

    @async_client_handler(check_no_op=True)
    async def signal(self, id: str, signal: str):
        return await self._parent.client.sandbox_v1.signal_bg_exec(
            *(await self._run_args()),
            id=id,
            body=V1SignalRequest(signal=signal),
        )

    @async_client_handler(check_no_op=True)
    async def delete(self, id: str):
        return await self._parent.client.sandbox_v1.delete_bg_exec(
            *(await self._run_args()),
            id=id,
        )


class _FsSubClient(_BaseSubClient):
    @client_handler(check_no_op=True)
    def read(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        timeout=None,
    ) -> FsReadResult:
        path = validate_remote_path(path)
        params = {"path": path, "offset": offset}
        if length is not None:
            params["length"] = length

        try:
            with requests.Session() as session:
                response = session.get(
                    self._url("fs/read"),
                    params=params,
                    **self._request_kwargs(
                        headers={"Accept": "application/octet-stream"},
                        timeout=timeout,
                    ),
                )
        except requests.RequestException as e:
            raise PolyaxonClientException("fs.read failed: {}".format(e)) from e

        self._raise_for_response(response, "fs.read")
        return FsReadResult(
            data=response.content,
            next_offset=int(response.headers.get("X-Polyaxon-Next-Offset", 0)),
            eof=to_bool(response.headers.get("X-Polyaxon-Eof"), handle_none=True),
        )

    @client_handler(check_no_op=True)
    def write(
        self,
        path: str,
        data: BytesLike,
        mode: int = 0o644,
        create: bool = True,
        append: bool = False,
        timeout=None,
    ) -> FsWriteResult:
        path = validate_remote_path(path)
        params = {
            "path": path,
            "mode": format_mode(mode),
            "create": format_query_bool(create),
            "append": format_query_bool(append),
        }
        try:
            with requests.Session() as session:
                response = session.post(
                    self._url("fs/write"),
                    params=params,
                    data=as_bytes(data),
                    **self._request_kwargs(
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/octet-stream",
                        },
                        timeout=timeout,
                    ),
                )
        except requests.RequestException as e:
            raise PolyaxonClientException("fs.write failed: {}".format(e)) from e

        self._raise_for_response(response, "fs.write")
        payload = orjson_loads(response.content) if response.content else {}
        return FsWriteResult(
            path=payload.get("path"),
            bytes_written=payload.get("bytes_written", 0),
            created=payload.get("created", False),
        )

    @client_handler(check_no_op=True)
    def read_bytes(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
    ) -> bytes:
        """Read a remote absolute POSIX path into memory."""
        return b"".join(
            self.iter_bytes(
                path=path,
                offset=offset,
                length=length,
                chunk_size=chunk_size,
                timeout=timeout,
            )
        )

    def iter_bytes(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
    ):
        """Yield chunks from a remote absolute POSIX path."""
        path = validate_remote_path(path)
        _validate_fs_read_args(offset=offset, length=length, chunk_size=chunk_size)

        def _iterator():
            if length == 0:
                return
            next_offset = offset
            remaining = length

            while True:
                result = self.read(
                    path=path,
                    offset=next_offset,
                    length=_next_read_length(remaining, chunk_size),
                    timeout=timeout,
                )
                data = result.data
                if remaining is not None:
                    data = data[:remaining]

                done = result.eof
                next_remaining = remaining

                if next_remaining is not None:
                    next_remaining -= len(data)
                    if next_remaining <= 0:
                        done = True

                if not done:
                    _validate_fs_read_advanced(
                        path=path,
                        next_offset=next_offset,
                        result=result,
                    )

                if data:
                    yield data

                if done:
                    break

                next_offset = result.next_offset
                remaining = next_remaining

        return _iterator()

    @client_handler(check_no_op=True)
    def write_bytes(
        self,
        path: str,
        data: BytesLike,
        mode: int = 0o644,
        create: bool = True,
        append: bool = False,
        timeout=None,
    ) -> FsWriteResult:
        return self.write(
            path=path,
            data=data,
            mode=mode,
            create=create,
            append=append,
            timeout=timeout,
        )

    @client_handler(check_no_op=True)
    def read_text(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        encoding: str = "utf-8",
        errors: str = "strict",
        timeout=None,
    ) -> str:
        """Read and decode bytes until EOF or the requested length.

        This buffers the requested range in memory. Use fs.read for explicit
        chunked reads.
        """
        return self.read_bytes(
            path=path,
            offset=offset,
            length=length,
            chunk_size=chunk_size,
            timeout=timeout,
        ).decode(encoding, errors=errors)

    @client_handler(check_no_op=True)
    def download_file(
        self,
        path: str,
        local_path,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
        create_parents: bool = True,
    ) -> str:
        """Download a remote absolute POSIX path to a local file.

        The local write uses a .part file followed by os.replace. This does not
        make any statement about remote-side atomicity.
        """
        path = validate_remote_path(path)
        destination = Path(local_path)
        if create_parents:
            destination.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = Path("{}.part".format(destination))

        try:
            with tmp_path.open("wb") as handle:
                for chunk in self.iter_bytes(
                    path=path,
                    offset=offset,
                    length=length,
                    chunk_size=chunk_size,
                    timeout=timeout,
                ):
                    handle.write(chunk)
            os.replace(tmp_path, destination)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

        return str(destination)

    @client_handler(check_no_op=True)
    def upload_file(
        self,
        local_path,
        path: str,
        mode: int = 0o644,
        create: bool = True,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
    ) -> FsWriteResult:
        """Upload a local file to a remote sandbox path.

        The remote path must be absolute. Uploads are not remote-atomic.
        Concurrent uploads to the same remote path are unsupported, and a
        mid-upload failure may leave a partial remote file. The mode only
        applies if the remote file is created.
        """
        path = validate_remote_path(path)
        _validate_file_chunk_size(chunk_size)
        source = Path(local_path)
        total = 0
        created = False
        wrote = False

        with source.open("rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk and wrote:
                    break

                result = self.write(
                    path=path,
                    data=chunk,
                    mode=mode,
                    create=create if not wrote else False,
                    append=wrote,
                    timeout=timeout,
                )
                if not wrote:
                    created = result.created
                total += result.bytes_written
                wrote = True

                if not chunk:
                    break

        return FsWriteResult(path=path, bytes_written=total, created=created)

    @client_handler(check_no_op=True)
    def write_text(
        self,
        path: str,
        data: str,
        mode: int = 0o644,
        create: bool = True,
        append: bool = False,
        encoding: str = "utf-8",
        errors: str = "strict",
        timeout=None,
    ) -> FsWriteResult:
        if not isinstance(data, str):
            raise TypeError("data must be a string")
        return self.write_bytes(
            path=path,
            data=data.encode(encoding, errors=errors),
            mode=mode,
            create=create,
            append=append,
            timeout=timeout,
        )

    @client_handler(check_no_op=True)
    def ls(
        self,
        path: str,
        recursive: Optional[bool] = None,
        max_entries: Optional[int] = None,
    ):
        path = validate_remote_path(path)
        return self._parent.client.sandbox_v1.fs_ls(
            *self._run_args(),
            path=path,
            recursive=recursive,
            max_entries=max_entries,
        )

    @client_handler(check_no_op=True)
    def mkdir(self, path: str, parents: bool = False, mode: int = 0o755):
        path = validate_remote_path(path)
        return self._parent.client.sandbox_v1.fs_mkdir(
            *self._run_args(),
            body=V1FsMkdirRequest(
                path=path,
                parents=parents,
                mode=format_mode(mode),
            ),
        )

    @client_handler(check_no_op=True)
    def rm(self, path: str, recursive: bool = False):
        path = validate_remote_path(path)
        return self._parent.client.sandbox_v1.fs_rm(
            *self._run_args(),
            path=path,
            recursive=recursive,
        )

    @client_handler(check_no_op=True)
    def stat(self, path: str):
        path = validate_remote_path(path)
        return self._parent.client.sandbox_v1.fs_stat(*self._run_args(), path=path)


class _AsyncFsSubClient(_FsSubClient, _AsyncBaseSubClient):
    @async_client_handler(check_no_op=True)
    async def read(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        timeout=None,
    ) -> FsReadResult:
        path = validate_remote_path(path)
        params = {"path": path, "offset": offset}
        if length is not None:
            params["length"] = length

        try:
            async with aiohttp.ClientSession(
                **self._session_kwargs(timeout=timeout)
            ) as session:
                async with session.get(
                    await self._url("fs/read"),
                    params=params,
                    **self._request_kwargs(
                        headers={"Accept": "application/octet-stream"}
                    ),
                ) as response:
                    data = await response.read()
                    await self._raise_for_response(response, data, "fs.read")
                    return FsReadResult(
                        data=data,
                        next_offset=int(
                            response.headers.get("X-Polyaxon-Next-Offset", 0)
                        ),
                        eof=to_bool(
                            response.headers.get("X-Polyaxon-Eof"), handle_none=True
                        ),
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise PolyaxonClientException("fs.read failed: {}".format(e)) from e

    @async_client_handler(check_no_op=True)
    async def write(
        self,
        path: str,
        data: BytesLike,
        mode: int = 0o644,
        create: bool = True,
        append: bool = False,
        timeout=None,
    ) -> FsWriteResult:
        path = validate_remote_path(path)
        params = {
            "path": path,
            "mode": format_mode(mode),
            "create": format_query_bool(create),
            "append": format_query_bool(append),
        }
        try:
            async with aiohttp.ClientSession(
                **self._session_kwargs(timeout=timeout)
            ) as session:
                async with session.post(
                    await self._url("fs/write"),
                    params=params,
                    data=as_bytes(data),
                    **self._request_kwargs(
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/octet-stream",
                        }
                    ),
                ) as response:
                    data = await response.read()
                    await self._raise_for_response(response, data, "fs.write")
                    payload = orjson_loads(data) if data else {}
                    return FsWriteResult(
                        path=payload.get("path"),
                        bytes_written=payload.get("bytes_written", 0),
                        created=payload.get("created", False),
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise PolyaxonClientException("fs.write failed: {}".format(e)) from e

    @async_client_handler(check_no_op=True)
    async def read_bytes(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
    ) -> bytes:
        """Read a remote absolute POSIX path into memory."""
        chunks = []
        async for chunk in self.iter_bytes(
            path=path,
            offset=offset,
            length=length,
            chunk_size=chunk_size,
            timeout=timeout,
        ):
            chunks.append(chunk)
        return b"".join(chunks)

    def iter_bytes(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
    ):
        """Yield chunks from a remote absolute POSIX path."""
        path = validate_remote_path(path)
        _validate_fs_read_args(offset=offset, length=length, chunk_size=chunk_size)

        async def _iterator():
            if length == 0:
                return
            next_offset = offset
            remaining = length

            while True:
                result = await self.read(
                    path=path,
                    offset=next_offset,
                    length=_next_read_length(remaining, chunk_size),
                    timeout=timeout,
                )
                data = result.data
                if remaining is not None:
                    data = data[:remaining]

                done = result.eof
                next_remaining = remaining

                if next_remaining is not None:
                    next_remaining -= len(data)
                    if next_remaining <= 0:
                        done = True

                if not done:
                    _validate_fs_read_advanced(
                        path=path,
                        next_offset=next_offset,
                        result=result,
                    )

                if data:
                    yield data

                if done:
                    break

                next_offset = result.next_offset
                remaining = next_remaining

        return _iterator()

    @async_client_handler(check_no_op=True)
    async def write_bytes(
        self,
        path: str,
        data: BytesLike,
        mode: int = 0o644,
        create: bool = True,
        append: bool = False,
        timeout=None,
    ) -> FsWriteResult:
        return await self.write(
            path=path,
            data=data,
            mode=mode,
            create=create,
            append=append,
            timeout=timeout,
        )

    @async_client_handler(check_no_op=True)
    async def read_text(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        encoding: str = "utf-8",
        errors: str = "strict",
        timeout=None,
    ) -> str:
        """Read and decode bytes until EOF or the requested length.

        This buffers the requested range in memory. Use fs.read for explicit
        chunked reads.
        """
        data = await self.read_bytes(
            path=path,
            offset=offset,
            length=length,
            chunk_size=chunk_size,
            timeout=timeout,
        )
        return data.decode(encoding, errors=errors)

    @async_client_handler(check_no_op=True)
    async def download_file(
        self,
        path: str,
        local_path,
        offset: int = 0,
        length: Optional[int] = None,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
        create_parents: bool = True,
    ) -> str:
        """Download a remote absolute POSIX path to a local file.

        The local file I/O is synchronous; async only covers the sandbox
        network requests.
        """
        path = validate_remote_path(path)
        destination = Path(local_path)
        if create_parents:
            destination.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = Path("{}.part".format(destination))

        try:
            with tmp_path.open("wb") as handle:
                async for chunk in self.iter_bytes(
                    path=path,
                    offset=offset,
                    length=length,
                    chunk_size=chunk_size,
                    timeout=timeout,
                ):
                    handle.write(chunk)
            os.replace(tmp_path, destination)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

        return str(destination)

    @async_client_handler(check_no_op=True)
    async def upload_file(
        self,
        local_path,
        path: str,
        mode: int = 0o644,
        create: bool = True,
        chunk_size: int = _DEFAULT_FILE_CHUNK_SIZE,
        timeout=None,
    ) -> FsWriteResult:
        """Upload a local file to a remote sandbox path.

        The remote path must be absolute. Uploads are not remote-atomic.
        Concurrent uploads to the same remote path are unsupported, and a
        mid-upload failure may leave a partial remote file. The mode only
        applies if the remote file is created. Local file I/O is synchronous;
        async only covers the sandbox network requests.
        """
        path = validate_remote_path(path)
        _validate_file_chunk_size(chunk_size)
        source = Path(local_path)
        total = 0
        created = False
        wrote = False

        with source.open("rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk and wrote:
                    break

                result = await self.write(
                    path=path,
                    data=chunk,
                    mode=mode,
                    create=create if not wrote else False,
                    append=wrote,
                    timeout=timeout,
                )
                if not wrote:
                    created = result.created
                total += result.bytes_written
                wrote = True

                if not chunk:
                    break

        return FsWriteResult(path=path, bytes_written=total, created=created)

    @async_client_handler(check_no_op=True)
    async def write_text(
        self,
        path: str,
        data: str,
        mode: int = 0o644,
        create: bool = True,
        append: bool = False,
        encoding: str = "utf-8",
        errors: str = "strict",
        timeout=None,
    ) -> FsWriteResult:
        if not isinstance(data, str):
            raise TypeError("data must be a string")
        return await self.write_bytes(
            path=path,
            data=data.encode(encoding, errors=errors),
            mode=mode,
            create=create,
            append=append,
            timeout=timeout,
        )

    @async_client_handler(check_no_op=True)
    async def ls(
        self,
        path: str,
        recursive: Optional[bool] = None,
        max_entries: Optional[int] = None,
    ):
        path = validate_remote_path(path)
        return await self._parent.client.sandbox_v1.fs_ls(
            *(await self._run_args()),
            path=path,
            recursive=recursive,
            max_entries=max_entries,
        )

    @async_client_handler(check_no_op=True)
    async def mkdir(self, path: str, parents: bool = False, mode: int = 0o755):
        path = validate_remote_path(path)
        return await self._parent.client.sandbox_v1.fs_mkdir(
            *(await self._run_args()),
            body=V1FsMkdirRequest(
                path=path,
                parents=parents,
                mode=format_mode(mode),
            ),
        )

    @async_client_handler(check_no_op=True)
    async def rm(self, path: str, recursive: bool = False):
        path = validate_remote_path(path)
        return await self._parent.client.sandbox_v1.fs_rm(
            *(await self._run_args()),
            path=path,
            recursive=recursive,
        )

    @async_client_handler(check_no_op=True)
    async def stat(self, path: str):
        path = validate_remote_path(path)
        return await self._parent.client.sandbox_v1.fs_stat(
            *(await self._run_args()),
            path=path,
        )


class _PtySubClient(_BaseSubClient):
    def _ws_url(self, id: str, replay_bytes: Optional[int] = None) -> str:
        url = self._url("pty/{}/ws".format(id))
        if replay_bytes is not None:
            url = "{}?{}".format(url, urlencode({"replay_bytes": replay_bytes}))
        return to_ws_url(url)

    @client_handler(check_no_op=True)
    def create(
        self,
        command=None,
        env=None,
        workdir: Optional[str] = None,
        cols: Optional[int] = 80,
        rows: Optional[int] = 24,
        tag: Optional[str] = None,
    ):
        return self._parent.client.sandbox_v1.create_pty(
            *self._run_args(),
            body=V1CreatePtyRequest(
                command=normalize_command(command) if command is not None else None,
                env=normalize_env(env),
                workdir=workdir,
                cols=cols,
                rows=rows,
                tag=tag,
            ),
        )

    @client_handler(check_no_op=True)
    def list(self, tag: Optional[str] = None):
        return self._parent.client.sandbox_v1.list_ptys(*self._run_args(), tag=tag)

    @client_handler(check_no_op=True)
    def get(self, id: str):
        return self._parent.client.sandbox_v1.get_pty(*self._run_args(), id=id)

    @client_handler(check_no_op=True)
    def delete(self, id: str):
        return self._parent.client.sandbox_v1.delete_pty(*self._run_args(), id=id)

    @client_handler(check_no_op=True)
    def resize(self, id: str, cols: int, rows: int):
        return self._parent.client.sandbox_v1.resize_pty(
            *self._run_args(),
            id=id,
            body=V1ResizePtyRequest(cols=cols, rows=rows),
        )

    @client_handler(check_no_op=True)
    def signal(self, id: str, signal: str):
        return self._parent.client.sandbox_v1.signal_pty(
            *self._run_args(),
            id=id,
            body=V1SignalRequest(signal=signal),
        )

    @client_handler(check_no_op=True)
    def attach(self, id: str, replay_bytes: Optional[int] = None, timeout=None):
        ws = None
        try:
            ws = sandbox_ws.connect(
                self._ws_url(id=id, replay_bytes=replay_bytes),
                headers=self._headers(),
                timeout=timeout,
            )
            attached_event = _validate_attached_message(sandbox_ws.recv_message(ws))
        except Exception:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass
            raise

        return sandbox_ws.SandboxPtyWSClient(
            ws=ws,
            attached_event=attached_event,
            resize=lambda cols, rows: self.resize(id, cols, rows),
            signal=lambda signal: self.signal(id, signal),
        )


class _AsyncPtySubClient(_PtySubClient, _AsyncBaseSubClient):
    async def _ws_url(self, id: str, replay_bytes: Optional[int] = None) -> str:
        url = await self._url("pty/{}/ws".format(id))
        if replay_bytes is not None:
            url = "{}?{}".format(url, urlencode({"replay_bytes": replay_bytes}))
        return to_ws_url(url)

    @async_client_handler(check_no_op=True)
    async def create(
        self,
        command=None,
        env=None,
        workdir: Optional[str] = None,
        cols: Optional[int] = 80,
        rows: Optional[int] = 24,
        tag: Optional[str] = None,
    ):
        return await self._parent.client.sandbox_v1.create_pty(
            *(await self._run_args()),
            body=V1CreatePtyRequest(
                command=normalize_command(command) if command is not None else None,
                env=normalize_env(env),
                workdir=workdir,
                cols=cols,
                rows=rows,
                tag=tag,
            ),
        )

    @async_client_handler(check_no_op=True)
    async def list(self, tag: Optional[str] = None):
        return await self._parent.client.sandbox_v1.list_ptys(
            *(await self._run_args()),
            tag=tag,
        )

    @async_client_handler(check_no_op=True)
    async def get(self, id: str):
        return await self._parent.client.sandbox_v1.get_pty(
            *(await self._run_args()),
            id=id,
        )

    @async_client_handler(check_no_op=True)
    async def delete(self, id: str):
        return await self._parent.client.sandbox_v1.delete_pty(
            *(await self._run_args()),
            id=id,
        )

    @async_client_handler(check_no_op=True)
    async def resize(self, id: str, cols: int, rows: int):
        return await self._parent.client.sandbox_v1.resize_pty(
            *(await self._run_args()),
            id=id,
            body=V1ResizePtyRequest(cols=cols, rows=rows),
        )

    @async_client_handler(check_no_op=True)
    async def signal(self, id: str, signal: str):
        return await self._parent.client.sandbox_v1.signal_pty(
            *(await self._run_args()),
            id=id,
            body=V1SignalRequest(signal=signal),
        )

    @async_client_handler(check_no_op=True)
    async def attach(self, id: str, replay_bytes: Optional[int] = None, timeout=None):
        session = None
        ws = None
        try:
            session, ws = await async_sandbox_ws.connect(
                await self._ws_url(id=id, replay_bytes=replay_bytes),
                headers=self._headers(),
                timeout=self._client_timeout(timeout),
            )
            attached_event = _validate_attached_message(
                await async_sandbox_ws.recv_message(ws)
            )
        except Exception:
            if ws is not None:
                try:
                    await ws.close()
                except Exception:
                    pass
            if session is not None:
                try:
                    await session.close()
                except Exception:
                    pass
            raise

        return async_sandbox_ws.AsyncSandboxPtyWSClient(
            session=session,
            ws=ws,
            attached_event=attached_event,
            resize=lambda cols, rows: self.resize(id, cols, rows),
            signal=lambda signal: self.signal(id, signal),
        )
