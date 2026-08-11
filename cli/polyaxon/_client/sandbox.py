import asyncio
from collections.abc import Mapping
from copy import deepcopy
import inspect
import os
from pathlib import Path
import requests
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode

import aiohttp

from clipped.utils.bools import to_bool
from clipped.utils.encoding import BytesLike, as_bytes, b64_data
from clipped.utils.http import absolute_uri, to_ws_url
from clipped.utils.json import orjson_dumps, orjson_loads
from clipped.utils.validation import validate_tags
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
from polyaxon._flow import V1Component, V1Operation, V1Plugins, V1RunKind, V1Service
from polyaxon._k8s.namespace import DEFAULT_NAMESPACE
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
from polyaxon._schemas.lifecycle import ManagedBy, V1Statuses
from polyaxon._sdk.schemas import (
    V1CreatePtyRequest,
    V1ExecBgRequest,
    V1ExecRequest,
    V1FsMkdirRequest,
    V1OperationBody,
    V1ResizePtyRequest,
    V1Run,
    V1RunSettings,
    V1SignalRequest,
)
from polyaxon._utils.fqn_utils import get_entity_full_name, split_owner_team_space
from polyaxon._utils.urls_utils import get_proxy_run_url
from polyaxon.api import SANDBOX_V1_LOCATION
from polyaxon.exceptions import PolyaxonClientException


_DEFAULT_FILE_CHUNK_SIZE = 64 * 1024


class SandboxClient(ClientMixin):
    """SandboxClient is a client to interact with a run's sandbox service.

    The sandbox service exposes process execution, filesystem access, and
    interactive PTY sessions inside the run's main container. Sandbox operations
    require a valid owner, project, and run uuid. To create a new sandbox-enabled
    service run, initialize the client with owner/project and call `create()`.

    If no values are passed to this class,
    Polyaxon will try to resolve the owner, project, and run uuid from the environment:
     * If you have a configured CLI, Polyaxon will use the configuration of the cli.
     * If you have a cached run using the CLI,
       the client will default to that cached run unless you override the values.
     * If you use this client in the context of a job or a service managed by Polyaxon,
       a configuration will be available to resolve the values based on that run.

    The functionality is split into sub-clients:
     * `process`: one-shot, streaming, and background command execution.
     * `fs`: filesystem reads, writes, transfers, and management.
     * `pty`: interactive PTY sessions over WebSocket.

    Example:
    ```python
    >>> from polyaxon.client import SandboxClient
    >>> client = SandboxClient(owner="acme", project="proj", run_uuid=run_uuid)
    >>> client.ping()
    >>> result = client.process.exec(command=["python", "-V"])
    >>> print(result.exit_code, result.stdout)
    ```

    Properties:
        project: str.
        owner: str.
        run_uuid: str.
        run_data: V1Run.
        namespace: str.
        settings: V1RunSettings.
        client: [PolyaxonClient](/docs/references/python-library/polyaxon-client/)
        process: the process execution sub-client.
        fs: the filesystem sub-client.
        pty: the PTY sub-client.

    Args:
        owner: str, optional, the owner is the username or
             the organization name owning this project.
        project: str, optional, project name owning the run(s).
        run_uuid: str, optional, run uuid.
        client: [PolyaxonClient](/docs/references/python-library/polyaxon-client/), optional,
             an instance of a configured client, if not passed,
             a new instance will be created based on the available environment.
        is_offline: bool, optional,
             To trigger the offline mode manually instead of depending on `POLYAXON_IS_OFFLINE`.
        no_op: bool, optional,
             To set the NO_OP mode manually instead of depending on `POLYAXON_NO_OP`.

    Raises:
        PolyaxonClientException: If the owner and/or project are not passed
             and Polyaxon cannot resolve the values from the environment.
    """

    @client_handler(check_no_op=True)
    def __init__(
        self,
        owner: Optional[str] = None,
        project: Optional[str] = None,
        run_uuid: Optional[str] = None,
        client: Optional[PolyaxonClient] = None,
        is_offline: Optional[bool] = None,
        no_op: Optional[bool] = None,
        manual_exceptions_handling: bool = False,
    ):
        self._manual_exceptions_handling = manual_exceptions_handling
        self._is_offline = get_global_or_inline_config(
            config_key="is_offline", config_value=is_offline, client=client
        )
        self._no_op = get_global_or_inline_config(
            config_key="no_op", config_value=no_op, client=client
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

        owner, team = split_owner_team_space(owner)
        self._set_client(client)
        self._owner = owner
        self._team = team
        self._project = project
        self._run_uuid = run_uuid
        self._run_data = V1Run.model_construct(
            owner=self._owner,
            project=self._project,
            uuid=self._run_uuid,
        )
        self._set_subclients()

    def _set_subclients(self):
        self.process = _ProcessSubClient(self)
        self.fs = _FsSubClient(self)
        self.pty = _PtySubClient(self)

    @property
    def run_uuid(self) -> Optional[str]:
        return self._run_uuid

    @property
    def namespace(self) -> str:
        if self.settings and self.settings.namespace:
            return self.settings.namespace
        return DEFAULT_NAMESPACE

    @property
    def run_data(self):
        return self._run_data

    @property
    def settings(self) -> Optional[V1RunSettings]:
        if not self.run_data:
            return None
        if self.run_data.settings and isinstance(self.run_data.settings, Mapping):
            self._run_data.settings = V1RunSettings(**self.run_data.settings)
        return self.run_data.settings

    def _set_namespace(self, namespace: str):
        if not self._run_data.settings:
            self._run_data.settings = V1RunSettings()
        self._run_data.settings.namespace = namespace

    def _require_run_uuid(self) -> str:
        if not self.run_uuid:
            raise PolyaxonClientException(
                "Please provide a valid run uuid or call `create()` first."
            )
        return self.run_uuid

    def _apply_created_run(self, response: V1Run):
        self._run_data = response
        self._run_uuid = self._run_data.uuid
        self._run_data.status = V1Statuses.CREATED
        self._namespace = None

    def _normalize_sandbox_operation_content(
        self,
        content: Optional[Union[str, Dict, V1Operation]],
        tmux: bool = False,
        ssh: bool = False,
    ) -> V1Operation:
        if content is None:
            return V1Operation(
                component=V1Component(
                    run=V1Service(),
                    plugins=V1Plugins(sandbox=True, tmux=tmux, ssh=ssh),
                )
            )
        if isinstance(content, Mapping):
            return V1Operation.from_dict(content)
        if isinstance(content, V1Operation):
            return deepcopy(content)
        if isinstance(content, str):
            return V1Operation.read(content)
        raise PolyaxonClientException("Received an invalid content: {}".format(content))

    def _build_sandbox_operation_content(
        self,
        content: Optional[Union[str, Dict, V1Operation]],
        tmux: bool = False,
        ssh: bool = False,
    ) -> str:
        operation = self._normalize_sandbox_operation_content(
            content, tmux=tmux, ssh=ssh
        )
        if not operation.component:
            raise PolyaxonClientException(
                "Sandbox creation requires inline component content."
            )
        component = operation.component
        if not component.run or component.run.kind != V1RunKind.SERVICE:
            kind = component.run.kind if component.run else None
            raise PolyaxonClientException(
                "Sandbox creation requires a service component, received `{}`.".format(
                    kind
                )
            )

        plugins = component.plugins
        if plugins and not isinstance(plugins, V1Plugins):
            raise PolyaxonClientException(
                "Sandbox creation cannot merge plugin references; "
                "provide inline plugins."
            )
        if not plugins:
            component.plugins = V1Plugins(sandbox=True, tmux=tmux, ssh=ssh)
        else:
            plugins.sandbox = True
        return operation.to_json()

    def _build_sandbox_create_body(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        content: Optional[Union[str, Dict, V1Operation]] = None,
        managed_by: Optional[ManagedBy] = None,
        is_managed: Optional[bool] = None,
        pending: Optional[str] = None,
        meta_info: Optional[Dict] = None,
    ) -> V1OperationBody:
        if not managed_by and is_managed is not None:
            managed_by = ManagedBy.AGENT if is_managed else ManagedBy.USER
        return V1OperationBody.model_construct(
            name=name,
            description=description,
            tags=tags,
            content=self._build_sandbox_operation_content(content),
            is_managed=is_managed,
            managed_by=managed_by,
            pending=pending,
            meta_info=meta_info,
        )

    @client_handler(check_no_op=True, check_offline=True)
    def create(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Union[str, List[str]]] = None,
        content: Optional[Union[str, Dict, V1Operation]] = None,
        managed_by: Optional[ManagedBy] = None,
        is_managed: Optional[bool] = None,
        pending: Optional[str] = None,
        meta_info: Optional[Dict] = None,
    ) -> V1Run:
        """Creates a new sandbox-enabled service run.

        A sandbox is not a separate Polyaxon resource. This method creates a
        regular `kind: service` run with `plugins.sandbox` enabled, then mutates
        this client to point at the returned run. After the run is approved,
        scheduled, and running, the same client can use `process`, `fs`, and `pty`.

        If `content` is not provided, the method builds a minimal service
        operation with `plugins.sandbox: true`. If `content` is provided, it
        must be inline service operation content so the client can verify the
        run kind and merge the sandbox plugin before submission.

        Example:
        ```python
        >>> from polyaxon.client import SandboxClient
        >>> client = SandboxClient(owner="acme", project="proj")
        >>> run = client.create(name="debug-sandbox")
        >>> print(run.uuid)
        >>> result = client.process.exec(command=["ls"])
        ```

        `create()` submits the service run but does not approve it, schedule it,
        or wait for readiness. After the run reaches `running`, call
        `client.ping()` before using the process, filesystem, or PTY sub-clients.

        Args:
            name: str, optional, run name.
            description: str, optional, run description.
            tags: str or List[str], optional, list of tags.
            content: str or Dict or V1Operation, optional, inline service operation
                 content. When provided, it must define a service component.
            is_managed: bool, flag to create a managed run.
            managed_by: ManagedBy, optional, service that manages the operation.
            pending: str, optional, pending state.
            meta_info: dict, optional, meta info to create the run with.

        Returns:
            V1Run, run instance from the response.
        """
        data = self._build_sandbox_create_body(
            name=name,
            description=description,
            tags=validate_tags(tags, validate_yaml=True),
            content=content,
            is_managed=is_managed,
            managed_by=managed_by,
            pending=pending,
            meta_info=meta_info,
        )
        response = self.client.runs_v1.create_run(
            owner=self.owner,
            project=self.project,
            body=data,
        )
        self._apply_created_run(response)
        return self.run_data

    @client_handler(check_no_op=True, check_offline=True)
    def get_namespace(self):
        """Fetches the run namespace.

        Returns:
            str, the namespace where the run is scheduled.
        """
        return self.client.runs_v1.get_run_namespace(
            self.owner,
            self.project,
            self._require_run_uuid(),
        ).namespace

    def _resolve_namespace(self) -> str:
        self._require_run_uuid()
        if self.settings and self.settings.namespace:
            return self.settings.namespace

        namespace = self.get_namespace()
        if not namespace:
            raise PolyaxonClientException(
                "Could not resolve sandbox run namespace for run `{}`.".format(
                    self.run_uuid
                )
            )
        self._set_namespace(namespace)
        return namespace

    def _sandbox_url(self, namespace: str, subpath: str) -> str:
        url = get_proxy_run_url(
            service=SANDBOX_V1_LOCATION,
            namespace=namespace,
            owner=self.owner,
            project=self.project,
            run_uuid=self._require_run_uuid(),
            subpath=subpath,
        )
        return absolute_uri(url=url, host=self.client.config.host)

    @client_handler(check_no_op=True)
    def ping(self):
        """Checks that the sandbox service is reachable and healthy.

        Example:
        ```python
        >>> response = client.ping()
        >>> print(response.status, response.version)
        ```

        Returns:
            V1PingResponse, with `status`, `version`, `uptime_ms`,
                 `last_activity`, `execs_running`, `ptys_running`, `ptys_attached`.
        """
        return self.client.sandbox_v1.ping(
            self._resolve_namespace(),
            self.owner,
            self.project,
            self._require_run_uuid(),
        )


class AsyncSandboxClient(SandboxClient):
    """AsyncSandboxClient is the async variant of the
    [SandboxClient](/docs/references/sandbox/client/#sandboxclient).

    It exposes the same API surface with coroutine methods and async iterators:
     * `process.exec_stream` returns an async context manager / async iterator.
     * Background exec handles expose awaitable methods and `async for` log iteration.
     * `pty.attach` returns an async WebSocket client.

    Example:
    ```python
    >>> from polyaxon.client import AsyncSandboxClient
    >>> client = AsyncSandboxClient(owner="acme", project="proj", run_uuid=run_uuid)
    >>> result = await client.process.exec(command=["python", "-V"])
    ```
    """

    _IS_ASYNC = True

    def _set_subclients(self):
        self.process = _AsyncProcessSubClient(self)
        self.fs = _AsyncFsSubClient(self)
        self.pty = _AsyncPtySubClient(self)

    @async_client_handler(check_no_op=True, check_offline=True)
    async def get_namespace(self):
        response = await self.client.runs_v1.get_run_namespace(
            self.owner,
            self.project,
            self._require_run_uuid(),
        )
        return response.namespace

    async def _resolve_namespace(self) -> str:
        self._require_run_uuid()
        if self.settings and self.settings.namespace:
            return self.settings.namespace

        namespace = await self.get_namespace()
        if not namespace:
            raise PolyaxonClientException(
                "Could not resolve sandbox run namespace for run `{}`.".format(
                    self.run_uuid
                )
            )
        self._set_namespace(namespace)
        return namespace

    @async_client_handler(check_no_op=True, check_offline=True)
    async def create(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Union[str, List[str]]] = None,
        content: Optional[Union[str, Dict, V1Operation]] = None,
        managed_by: Optional[ManagedBy] = None,
        is_managed: Optional[bool] = None,
        pending: Optional[str] = None,
        meta_info: Optional[Dict] = None,
    ) -> V1Run:
        """Creates a new sandbox-enabled service run asynchronously.

        A sandbox is not a separate Polyaxon resource. This method creates a
        regular `kind: service` run with `plugins.sandbox` enabled, then mutates
        this client to point at the returned run. After the run is approved,
        scheduled, and running, the same client can use `process`, `fs`, and `pty`.

        If `content` is not provided, the method builds a minimal service
        operation with `plugins.sandbox: true`. If `content` is provided, it
        must be inline service operation content so the client can verify the
        run kind and merge the sandbox plugin before submission.

        Example:
        ```python
        >>> from polyaxon.client import AsyncSandboxClient
        >>> client = AsyncSandboxClient(owner="acme", project="proj")
        >>> run = await client.create(name="debug-sandbox")
        >>> print(run.uuid)
        >>> result = client.process.exec(command=["ls"])
        ```

        `create()` submits the service run but does not approve it, schedule it,
        or wait for readiness. After the run reaches `running`, call
        `await client.ping()` before using the process, filesystem, or PTY sub-clients.

        Args:
            name: str, optional, run name.
            description: str, optional, run description.
            tags: str or List[str], optional, list of tags.
            content: str or Dict or V1Operation, optional, inline service operation
                 content. When provided, it must define a service component.
            is_managed: bool, flag to create a managed run.
            managed_by: ManagedBy, optional, service that manages the operation.
            pending: str, optional, pending state.
            meta_info: dict, optional, meta info to create the run with.

        Returns:
            V1Run, run instance from the response.
        """
        data = self._build_sandbox_create_body(
            name=name,
            description=description,
            tags=validate_tags(tags, validate_yaml=True),
            content=content,
            is_managed=is_managed,
            managed_by=managed_by,
            pending=pending,
            meta_info=meta_info,
        )
        response = await self.client.runs_v1.create_run(
            owner=self.owner,
            project=self.project,
            body=data,
        )
        self._apply_created_run(response)
        return self.run_data

    @async_client_handler(check_no_op=True)
    async def ping(self):
        return await self.client.sandbox_v1.ping(
            await self._resolve_namespace(),
            self.owner,
            self.project,
            self._require_run_uuid(),
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
            self._parent._resolve_namespace(),
            self._parent.owner,
            self._parent.project,
            self._parent.run_uuid,
        )

    def _url(self, subpath: str) -> str:
        return self._parent._sandbox_url(self._parent._resolve_namespace(), subpath)

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
            await self._parent._resolve_namespace(),
            self._parent.owner,
            self._parent.project,
            self._parent.run_uuid,
        )

    async def _url(self, subpath: str) -> str:
        return self._parent._sandbox_url(
            await self._parent._resolve_namespace(), subpath
        )

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
    """SandboxBgExec is a handle for a background command started
    with `process.exec_bg`.

    It wraps the started exec's id and exposes convenience methods to poll
    status, read logs, signal, and wait for completion.

    Example:
    ```python
    >>> bg = client.process.exec_bg(command=["sh", "-lc", "sleep 2; echo done"])
    >>> print(bg.id, bg.pid, bg.started_at, bg.tag)
    >>> for chunk in bg.iter_stdout(timeout=10, interval=0.2):
    >>>     print(chunk, end="")
    >>> status = bg.wait(timeout=10)
    >>> print(status.state, status.exit_code)
    ```

    Properties:
        id: str, the background exec id.
        exec_id: str, alias of `id`.
        pid: int, the process pid.
        started_at: datetime, when the process started.
        tag: str, the optional tag passed at start time.
        start: V1ExecBgStart, the raw start response.
    """

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
        """Fetches the current status of the background exec.

        Returns:
            V1ExecBgStatus, with `state`, `exit_code`, `signal`,
                 `started_at`, `finished_at`, `duration_ms`,
                 `stdout_bytes`, `stderr_bytes`, `tag`.
        """
        return self._process.get(self.exec_id)

    def logs(
        self,
        stream: Optional[str] = None,
        offset: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ):
        """Fetches one page of captured logs for the background exec.

        Args:
            stream: str, optional, `stdout` or `stderr`.
            offset: int, optional, byte offset to read from.
            max_bytes: int, optional, max bytes to return in this page.

        Returns:
            V1ExecBgLogs, with `data`, `next_offset`, `eof`, and `state`.
        """
        return self._process.logs(
            self.exec_id,
            stream=stream,
            offset=offset,
            max_bytes=max_bytes,
        )

    def signal(self, signal: str):
        """Sends a signal to the background exec.

        Args:
            signal: str, the signal name, e.g. `SIGTERM` or `SIGKILL`.
        """
        return self._process.signal(self.exec_id, signal)

    def kill(self, signal: str = "SIGTERM"):
        """Sends a termination signal to the background exec.

        Alias of `signal` with a default of `SIGTERM`.

        Args:
            signal: str, optional, the signal name, default: `SIGTERM`.
        """
        return self.signal(signal)

    def delete(self):
        """Deletes the background exec record and its captured logs."""
        return self._process.delete(self.exec_id)

    def stdout(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> str:
        """Returns the captured stdout data as a string.

        This is a convenience that buffers the requested range in memory.
        Use `iter_stdout` to follow logs incrementally.

        Args:
            offset: int, optional, byte offset to read from.
            max_bytes: int, optional, max bytes to return.

        Returns:
            str
        """
        return _log_data(self.logs(stream="stdout", offset=offset, max_bytes=max_bytes))

    def stderr(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> str:
        """Returns the captured stderr data as a string.

        This is a convenience that buffers the requested range in memory.
        Use `iter_stderr` to follow logs incrementally.

        Args:
            offset: int, optional, byte offset to read from.
            max_bytes: int, optional, max bytes to return.

        Returns:
            str
        """
        return _log_data(self.logs(stream="stderr", offset=offset, max_bytes=max_bytes))

    def output(
        self,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ) -> SandboxBgOutput:
        """Returns both captured stdout and stderr, buffered in memory.

        Args:
            offset: int, optional, byte offset to read from.
            max_bytes: int, optional, max bytes to return per stream.

        Returns:
            SandboxBgOutput, with `stdout` and `stderr` strings.
        """
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
        """Iterates over the captured logs by polling with increasing offsets.

        The iterator yields data chunks as they become available and stops
        when the exec reaches a terminal state and all data is consumed.

        Example:
        ```python
        >>> for chunk in bg.iter_logs(stream="stdout", timeout=10, interval=0.2):
        >>>     print(chunk, end="")
        ```

        Args:
            stream: str, optional, `stdout` or `stderr`, default: `stdout`.
            offset: int, optional, byte offset to start from.
            max_bytes: int, optional, max bytes per polling request.
            timeout: int, optional, max seconds to wait before raising.
            interval: float, optional, seconds between polls, default: 1.0.

        Yields:
            str, log data chunks.

        Raises:
            PolyaxonClientException: If the timeout is reached or the server
                 returns inconsistent offsets.
        """
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
        """Iterates over the captured stdout logs. See `iter_logs`."""
        return self.iter_logs(stream="stdout", **kwargs)

    def iter_stderr(self, **kwargs):
        """Iterates over the captured stderr logs. See `iter_logs`."""
        return self.iter_logs(stream="stderr", **kwargs)

    def wait(self, timeout=None, interval: float = 1.0):
        """Polls the background exec until it reaches a terminal state.

        Terminal states are: `exited`, `signaled`, `timed_out`,
        `failed_to_start`, `orphaned`.

        Args:
            timeout: int, optional, max seconds to wait before raising.
                 A timeout of 0 polls exactly once.
            interval: float, optional, seconds between polls, default: 1.0.

        Returns:
            V1ExecBgStatus, the terminal status.

        Raises:
            PolyaxonClientException: If the timeout is reached before the
                 exec terminates.
        """
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
    """Async variant of `SandboxBgExec`.

    All methods are coroutines and `iter_logs`/`iter_stdout`/`iter_stderr`
    return async iterators.

    Example:
    ```python
    >>> bg = await client.process.exec_bg(command=["sh", "-lc", "echo bg"])
    >>> async for chunk in bg.iter_stdout(timeout=10):
    >>>     print(chunk, end="")
    >>> status = await bg.wait(timeout=10)
    ```
    """

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
    """Process execution sub-client, accessed via `client.process`."""

    @client_handler(check_no_op=True)
    def exec(
        self,
        command,
        env=None,
        workdir: Optional[str] = None,
        stdin: Optional[BytesLike] = None,
        timeout_ms: Optional[int] = None,
    ):
        """Runs a command to completion and returns the buffered result.

        The command must be an iterable of strings, plain strings are
        rejected. Use `exec_stream` for incremental output and `exec_bg`
        for detached commands.

        Example:
        ```python
        >>> result = client.process.exec(
        >>>     command=["python", "-c", "import os; print(os.getenv('MSG'))"],
        >>>     env={"MSG": "hello"},
        >>>     workdir="/tmp",
        >>>     timeout_ms=10_000,
        >>> )
        >>> print(result.exit_code, result.stdout, result.stderr)
        ```

        Args:
            command: List[str], the command and its arguments.
            env: Dict[str, str], optional, environment variables to set.
                 Values must be strings. `POLYAXON_*` keys are rejected
                 by the server.
            workdir: str, optional, working directory for the command.
            stdin: str or bytes, optional, data to pass to the command's stdin.
            timeout_ms: int, optional, server-side execution timeout
                 in milliseconds.

        Returns:
            V1ExecResult, with `exit_code`, `stdout`, `stderr`, `signal`,
                 `duration_ms`, `timed_out`, `stdout_truncated`,
                 `stderr_truncated`.

        Raises:
            TypeError: If the command or env values have the wrong shape.
        """
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
        """Runs a command and streams its output as server-sent events.

        Returns an iterator that is also a context manager. Breaking out of
        the loop early inside a `with` block closes the HTTP response.
        Events are dicts with a `type` key: `stdout`, `stderr`, `error`,
        and `execution_complete`.

        Example:
        ```python
        >>> with client.process.exec_stream(
        >>>     command=["sh", "-lc", "echo one; echo two"],
        >>> ) as events:
        >>>     for event in events:
        >>>         print(event)
        >>>         if event.get("type") == "execution_complete":
        >>>             break
        ```

        Args:
            command: List[str], the command and its arguments.
            env: Dict[str, str], optional, environment variables to set.
            workdir: str, optional, working directory for the command.
            stdin: str or bytes, optional, data to pass to the command's stdin.
            timeout_ms: int, optional, server-side execution timeout
                 in milliseconds.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            An SSE iterator and context manager yielding event dicts.

        Raises:
            PolyaxonClientException: If the request or the stream fails.
        """
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
        """Starts a detached background command and returns a handle.

        The command keeps running after this call returns. Use the returned
        handle to poll status, read logs, signal, and wait.

        Example:
        ```python
        >>> bg = client.process.exec_bg(
        >>>     command=["sh", "-lc", "for i in 1 2 3; do echo tick-$i; sleep 1; done"],
        >>>     tag="my-job",
        >>> )
        >>> status = bg.wait(timeout=10)
        >>> print(status.state, status.exit_code)
        ```

        Args:
            command: List[str], the command and its arguments.
            env: Dict[str, str], optional, environment variables to set.
            workdir: str, optional, working directory for the command.
            stdin: str or bytes, optional, data to pass to the command's stdin.
            timeout_ms: int, optional, server-side execution timeout
                 in milliseconds.
            tag: str, optional, a label to filter execs in `list`.

        Returns:
            SandboxBgExec, a handle for the started command with `id`, `pid`,
                 `started_at`, and `tag` properties, and methods to poll
                 status, read logs, signal, and wait, documented below.
        """
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
        """Lists background execs.

        Args:
            tag: str, optional, only return execs started with this tag.

        Returns:
            V1ExecBgList, with `execs`, a list of V1ExecBgStatus.
        """
        return self._parent.client.sandbox_v1.list_bg_execs(
            *self._run_args(),
            tag=tag,
        )

    @client_handler(check_no_op=True)
    def get(self, id: str):
        """Fetches the status of a background exec by id.

        Args:
            id: str, the background exec id.

        Returns:
            V1ExecBgStatus
        """
        return self._parent.client.sandbox_v1.get_bg_exec(*self._run_args(), id=id)

    @client_handler(check_no_op=True)
    def logs(
        self,
        id: str,
        stream: Optional[str] = None,
        offset: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ):
        """Fetches one page of captured logs for a background exec.

        Args:
            id: str, the background exec id.
            stream: str, optional, `stdout` or `stderr`.
            offset: int, optional, byte offset to read from.
            max_bytes: int, optional, max bytes to return in this page.

        Returns:
            V1ExecBgLogs, with `data`, `next_offset`, `eof`, and `state`.
        """
        return self._parent.client.sandbox_v1.get_bg_exec_logs(
            *self._run_args(),
            id=id,
            stream=stream,
            offset=offset,
            max_bytes=max_bytes,
        )

    @client_handler(check_no_op=True)
    def signal(self, id: str, signal: str):
        """Sends a signal to a background exec.

        Args:
            id: str, the background exec id.
            signal: str, the signal name, e.g. `SIGTERM` or `SIGKILL`.
        """
        return self._parent.client.sandbox_v1.signal_bg_exec(
            *self._run_args(),
            id=id,
            body=V1SignalRequest(signal=signal),
        )

    @client_handler(check_no_op=True)
    def delete(self, id: str):
        """Deletes a background exec record and its captured logs.

        Args:
            id: str, the background exec id.
        """
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
    """Filesystem sub-client, accessed via `client.fs`.

    All remote paths must be absolute POSIX paths; relative paths are
    rejected client-side before any network I/O.
    """

    @client_handler(check_no_op=True)
    def read(
        self,
        path: str,
        offset: int = 0,
        length: Optional[int] = None,
        timeout=None,
    ) -> FsReadResult:
        """Reads one page of bytes from a remote file.

        This exposes the server paging contract directly. Use `read_bytes`,
        `read_text`, or `iter_bytes` for higher-level reads.

        Example:
        ```python
        >>> result = client.fs.read("/tmp/data.bin", offset=0, length=1024)
        >>> print(result.data, result.next_offset, result.eof)
        ```

        Args:
            path: str, an absolute POSIX path on the sandbox.
            offset: int, optional, byte offset to read from.
            length: int, optional, max bytes to return in this page.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            FsReadResult, with `data` bytes, `next_offset`, and `eof`.

        Raises:
            ValueError: If the path is not absolute or arguments are invalid.
            PolyaxonClientException: If the request fails.
        """
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
        """Writes bytes to a remote file in a single request.

        Use `upload_file` for chunked transfers of local files.

        Example:
        ```python
        >>> result = client.fs.write("/tmp/hello.txt", b"hello\\n")
        >>> print(result.path, result.bytes_written, result.created)
        ```

        Args:
            path: str, an absolute POSIX path on the sandbox.
            data: str or bytes, the content to write.
            mode: int, optional, file mode if the file is created,
                 default: `0o644`.
            create: bool, optional, create the file if it does not exist,
                 default: True.
            append: bool, optional, append instead of overwrite,
                 default: False.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            FsWriteResult, with `path`, `bytes_written`, and `created`.

        Raises:
            ValueError: If the path is not absolute.
            PolyaxonClientException: If the request fails.
        """
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
        """Reads a remote file into memory as bytes.

        This buffers the requested range in memory. Use `iter_bytes` for
        large files.

        Args:
            path: str, an absolute POSIX path on the sandbox.
            offset: int, optional, byte offset to start from.
            length: int, optional, max bytes to read, default: until EOF.
            chunk_size: int, optional, bytes per request, default: 64KiB.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            bytes
        """
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
        """Iterates over a remote file's content in chunks.

        This is the lower-memory option for large files.

        Example:
        ```python
        >>> for chunk in client.fs.iter_bytes("/tmp/data.bin", chunk_size=1024):
        >>>     process(chunk)
        ```

        Args:
            path: str, an absolute POSIX path on the sandbox.
            offset: int, optional, byte offset to start from.
            length: int, optional, max bytes to read, default: until EOF.
            chunk_size: int, optional, bytes per request, default: 64KiB.
            timeout: int, optional, client-side request timeout in seconds.

        Yields:
            bytes, file content chunks.

        Raises:
            ValueError: If the path is not absolute or arguments are invalid.
            PolyaxonClientException: If the server returns non-advancing
                 offsets.
        """
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
        """Writes bytes to a remote file. Alias of `write`.

        Args:
            path: str, an absolute POSIX path on the sandbox.
            data: str or bytes, the content to write.
            mode: int, optional, file mode if the file is created,
                 default: `0o644`.
            create: bool, optional, create the file if it does not exist,
                 default: True.
            append: bool, optional, append instead of overwrite,
                 default: False.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            FsWriteResult, with `path`, `bytes_written`, and `created`.
        """
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
        """Reads a remote file and decodes it as text.

        This buffers the requested range in memory. Use `read` for explicit
        chunked reads.

        Example:
        ```python
        >>> print(client.fs.read_text("/tmp/hello.txt"))
        ```

        Args:
            path: str, an absolute POSIX path on the sandbox.
            offset: int, optional, byte offset to start from.
            length: int, optional, max bytes to read, default: until EOF.
            chunk_size: int, optional, bytes per request, default: 64KiB.
            encoding: str, optional, text encoding, default: `utf-8`.
            errors: str, optional, decoding error handling, default: `strict`.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            str
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
        """Downloads a remote file to a local path.

        The local write uses a `.part` file followed by `os.replace`, so the
        local destination is never left partially written. This makes no
        statement about remote-side atomicity.

        Example:
        ```python
        >>> client.fs.download_file("/tmp/results.json", "results.json")
        ```

        Args:
            path: str, an absolute POSIX path on the sandbox.
            local_path: str or Path, the local destination.
            offset: int, optional, remote byte offset to start from.
            length: int, optional, max bytes to download, default: until EOF.
            chunk_size: int, optional, bytes per request, default: 64KiB.
            timeout: int, optional, client-side request timeout in seconds.
            create_parents: bool, optional, create local parent directories,
                 default: True.

        Returns:
            str, the local destination path.
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
        """Uploads a local file to a remote sandbox path.

        Uploads are chunked but not remote-atomic: a mid-upload failure may
        leave a partial remote file. Concurrent uploads to the same remote
        path are unsupported. The mode only applies if the remote file is
        created.

        Example:
        ```python
        >>> client.fs.upload_file("data.csv", "/tmp/data.csv")
        ```

        Args:
            local_path: str or Path, the local file to upload.
            path: str, an absolute POSIX path on the sandbox.
            mode: int, optional, file mode if the remote file is created,
                 default: `0o644`.
            create: bool, optional, create the remote file if it does not
                 exist, default: True.
            chunk_size: int, optional, bytes per request, default: 64KiB.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            FsWriteResult, with `path`, `bytes_written`, and `created`.
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
        """Encodes a string and writes it to a remote file.

        Example:
        ```python
        >>> client.fs.write_text("/tmp/hello.txt", "hello\\n")
        ```

        Args:
            path: str, an absolute POSIX path on the sandbox.
            data: str, the text to write.
            mode: int, optional, file mode if the file is created,
                 default: `0o644`.
            create: bool, optional, create the file if it does not exist,
                 default: True.
            append: bool, optional, append instead of overwrite,
                 default: False.
            encoding: str, optional, text encoding, default: `utf-8`.
            errors: str, optional, encoding error handling, default: `strict`.
            timeout: int, optional, client-side request timeout in seconds.

        Returns:
            FsWriteResult, with `path`, `bytes_written`, and `created`.

        Raises:
            TypeError: If data is not a string.
        """
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
        """Lists a remote directory.

        Args:
            path: str, an absolute POSIX path on the sandbox.
            recursive: bool, optional, list entries recursively.
            max_entries: int, optional, max entries to return.

        Returns:
            V1FsListResult, with `path`, `entries`, and `truncated`.
        """
        path = validate_remote_path(path)
        return self._parent.client.sandbox_v1.fs_ls(
            *self._run_args(),
            path=path,
            recursive=recursive,
            max_entries=max_entries,
        )

    @client_handler(check_no_op=True)
    def mkdir(self, path: str, parents: bool = False, mode: int = 0o755):
        """Creates a remote directory.

        Args:
            path: str, an absolute POSIX path on the sandbox.
            parents: bool, optional, create parent directories as needed,
                 default: False.
            mode: int, optional, directory mode, default: `0o755`.

        Returns:
            V1FsPathResult, with the created `path`.
        """
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
        """Removes a remote file or directory.

        Args:
            path: str, an absolute POSIX path on the sandbox.
            recursive: bool, optional, remove directories recursively,
                 default: False.

        Returns:
            V1FsPathResult, with the removed `path`.
        """
        path = validate_remote_path(path)
        return self._parent.client.sandbox_v1.fs_rm(
            *self._run_args(),
            path=path,
            recursive=recursive,
        )

    @client_handler(check_no_op=True)
    def stat(self, path: str):
        """Fetches metadata for a remote file or directory.

        Args:
            path: str, an absolute POSIX path on the sandbox.

        Returns:
            V1FsStatResult, with `path`, `type`, `size`, `mtime`, `mode`,
                 `uid`, `gid`, `symlink_target`.
        """
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
    """PTY sub-client, accessed via `client.pty`.

    Manages interactive PTY sessions inside the sandbox and attaches to
    them over WebSocket.
    """

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
        """Creates a new PTY session.

        Example:
        ```python
        >>> pty = client.pty.create(command=["sh"], cols=80, rows=24)
        >>> print(pty.pty_id, pty.state)
        ```

        Args:
            command: List[str], optional, the command to run in the PTY,
                 default: the server's default shell.
            env: Dict[str, str], optional, environment variables to set.
            workdir: str, optional, working directory for the session.
            cols: int, optional, terminal columns, default: 80.
            rows: int, optional, terminal rows, default: 24.
            tag: str, optional, a label to filter sessions in `list`.

        Returns:
            V1Pty, with `pty_id`, `pid`, `state`, `attached`, `cols`,
                 `rows`, `tag`, and activity timestamps.
        """
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
        """Lists PTY sessions.

        Args:
            tag: str, optional, only return sessions created with this tag.

        Returns:
            V1PtyList, with `sessions`, a list of V1Pty.
        """
        return self._parent.client.sandbox_v1.list_ptys(*self._run_args(), tag=tag)

    @client_handler(check_no_op=True)
    def get(self, id: str):
        """Fetches a PTY session by id.

        Args:
            id: str, the PTY session id.

        Returns:
            V1Pty
        """
        return self._parent.client.sandbox_v1.get_pty(*self._run_args(), id=id)

    @client_handler(check_no_op=True)
    def delete(self, id: str):
        """Terminates and deletes a PTY session.

        Args:
            id: str, the PTY session id.
        """
        return self._parent.client.sandbox_v1.delete_pty(*self._run_args(), id=id)

    @client_handler(check_no_op=True)
    def resize(self, id: str, cols: int, rows: int):
        """Resizes a PTY session's terminal.

        Args:
            id: str, the PTY session id.
            cols: int, terminal columns.
            rows: int, terminal rows.
        """
        return self._parent.client.sandbox_v1.resize_pty(
            *self._run_args(),
            id=id,
            body=V1ResizePtyRequest(cols=cols, rows=rows),
        )

    @client_handler(check_no_op=True)
    def signal(self, id: str, signal: str):
        """Sends a signal to a PTY session's process.

        Args:
            id: str, the PTY session id.
            signal: str, the signal name, e.g. `SIGTERM` or `SIGKILL`.
        """
        return self._parent.client.sandbox_v1.signal_pty(
            *self._run_args(),
            id=id,
            body=V1SignalRequest(signal=signal),
        )

    @client_handler(check_no_op=True)
    def attach(self, id: str, replay_bytes: Optional[int] = None, timeout=None):
        """Attaches to a PTY session over WebSocket.

        The initial `attached` control event is consumed before this method
        returns; a bad initial frame closes the socket and raises.

        The returned client is a context manager and exposes:
         * `send_stdin(data)`: sends bytes to the PTY's stdin.
         * `recv()`: receives the next frame, bytes for raw PTY output,
           dicts for JSON control events.
         * `resize(cols, rows)`: resizes the terminal.
         * `signal(signal)` / `kill(signal="SIGTERM")`: signals the process.
         * `attached_event`: the initial attached control event.
         * `close()`: closes the WebSocket.

        Example:
        ```python
        >>> pty = client.pty.create(command=["sh"])
        >>> with client.pty.attach(pty.pty_id, replay_bytes=1024) as ws:
        >>>     ws.send_stdin(b"echo ready\\n")
        >>>     frame = ws.recv()
        ```

        Args:
            id: str, the PTY session id.
            replay_bytes: int, optional, bytes of recent output to replay
                 on attach.
            timeout: int, optional, connection timeout in seconds.

        Returns:
            SandboxPtyWSClient, a connected PTY WebSocket client.

        Raises:
            PolyaxonClientException: If the attach handshake fails.
        """
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
