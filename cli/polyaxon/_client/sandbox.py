import asyncio
import inspect
import requests
from typing import Optional

import aiohttp

from clipped.utils.bools import to_bool
from clipped.utils.encoding import BytesLike, as_bytes, b64_data
from clipped.utils.http import absolute_uri
from clipped.utils.json import orjson_dumps, orjson_loads
from polyaxon import settings
from polyaxon._client.client import PolyaxonClient
from polyaxon._client.decorators import (
    async_client_handler,
    client_handler,
    get_global_or_inline_config,
)
from polyaxon._client.mixin import ClientMixin
from polyaxon._env_vars.getters import (
    get_project_error_message,
    get_project_or_local,
    get_run_or_local,
)
from polyaxon._sandbox.client_utils import (
    FsReadResult,
    FsWriteResult,
    SseFrameBuffer,
    format_mode,
    normalize_command,
    normalize_env,
    parse_error_message,
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
        session=None,
    ):
        body = V1ExecRequest(
            command=normalize_command(command),
            env=normalize_env(env),
            workdir=workdir,
            stdin=b64_data(stdin),
            timeout_ms=timeout_ms,
        )
        session = session or requests.Session()
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
        return self._parent.client.sandbox_v1.exec_bg(
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
        session=None,
    ):
        body = V1ExecRequest(
            command=normalize_command(command),
            env=normalize_env(env),
            workdir=workdir,
            stdin=b64_data(stdin),
            timeout_ms=timeout_ms,
        )
        session = session or aiohttp.ClientSession(
            **self._session_kwargs(timeout=timeout)
        )
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
        return await self._parent.client.sandbox_v1.exec_bg(
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
        params = {
            "path": path,
            "mode": format_mode(mode),
            "create": create,
            "append": append,
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
    def ls(
        self,
        path: Optional[str] = None,
        recursive: Optional[bool] = None,
        max_entries: Optional[int] = None,
    ):
        return self._parent.client.sandbox_v1.fs_ls(
            *self._run_args(),
            path=path,
            recursive=recursive,
            max_entries=max_entries,
        )

    @client_handler(check_no_op=True)
    def mkdir(self, path: str, parents: bool = False, mode: int = 0o755):
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
        return self._parent.client.sandbox_v1.fs_rm(
            *self._run_args(),
            path=path,
            recursive=recursive,
        )

    @client_handler(check_no_op=True)
    def stat(self, path: str):
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
        params = {
            "path": path,
            "mode": format_mode(mode),
            "create": create,
            "append": append,
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
    async def ls(
        self,
        path: Optional[str] = None,
        recursive: Optional[bool] = None,
        max_entries: Optional[int] = None,
    ):
        return await self._parent.client.sandbox_v1.fs_ls(
            *(await self._run_args()),
            path=path,
            recursive=recursive,
            max_entries=max_entries,
        )

    @async_client_handler(check_no_op=True)
    async def mkdir(self, path: str, parents: bool = False, mode: int = 0o755):
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
        return await self._parent.client.sandbox_v1.fs_rm(
            *(await self._run_args()),
            path=path,
            recursive=recursive,
        )

    @async_client_handler(check_no_op=True)
    async def stat(self, path: str):
        return await self._parent.client.sandbox_v1.fs_stat(
            *(await self._run_args()),
            path=path,
        )


class _PtySubClient(_BaseSubClient):
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


class _AsyncPtySubClient(_PtySubClient, _AsyncBaseSubClient):
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
