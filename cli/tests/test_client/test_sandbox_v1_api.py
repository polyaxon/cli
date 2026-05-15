import json
from mock import patch
import pytest
from unittest.mock import AsyncMock

from polyaxon import schemas
from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.api import SandboxV1Api
from polyaxon._sdk.async_client.api_client import AsyncApiClient
from polyaxon._sdk.schemas import (
    V1CreatePtyRequest,
    V1ExecBgList,
    V1ExecBgLogs,
    V1ExecBgRequest,
    V1ExecBgStart,
    V1ExecBgStatus,
    V1ExecRequest,
    V1ExecResult,
    V1FsEntry,
    V1FsListResult,
    V1FsMkdirRequest,
    V1FsPathResult,
    V1FsStatResult,
    V1PingResponse,
    V1Pty,
    V1PtyList,
    V1ResizePtyRequest,
    V1SignalRequest,
)
from polyaxon._sdk.sync_client.api_client import ApiClient
from polyaxon._utils.test_utils import patch_settings


SANDBOX_SCHEMAS = [
    V1CreatePtyRequest,
    V1ExecBgList,
    V1ExecBgLogs,
    V1ExecBgRequest,
    V1ExecBgStart,
    V1ExecBgStatus,
    V1ExecRequest,
    V1ExecResult,
    V1FsEntry,
    V1FsListResult,
    V1FsMkdirRequest,
    V1FsPathResult,
    V1FsStatResult,
    V1PingResponse,
    V1Pty,
    V1PtyList,
    V1ResizePtyRequest,
    V1SignalRequest,
]


class _Response:
    def __init__(self, status, data):
        self.status = status
        self.data = json.dumps(data).encode("utf-8")

    def getheader(self, name):
        if name.lower() == "content-type":
            return "application/json"
        return None

    def getheaders(self):
        return {}


@pytest.mark.client_mark
def test_public_sandbox_schema_exports():
    for schema_cls in SANDBOX_SCHEMAS:
        assert getattr(schemas, schema_cls.__name__) is schema_cls


@pytest.mark.client_mark
def test_exec_bg_202_response_deserializes():
    patch_settings()
    api_client = ApiClient(ClientConfig(host="http://polyaxon").sdk_config)
    response = _Response(
        202,
        {
            "exec_id": "exec-1",
            "pid": 12,
            "started_at": "2026-01-01T00:00:00Z",
            "tag": "build",
        },
    )

    with patch.object(api_client, "request", return_value=response):
        result = SandboxV1Api(api_client).exec_bg(
            namespace="ns",
            owner="owner",
            project="project",
            uuid="run-uuid",
            body=V1ExecBgRequest(command=["echo", "hi"]),
        )

    assert isinstance(result, V1ExecBgStart)
    assert result.exec_id == "exec-1"
    assert result.pid == 12
    assert result.tag == "build"


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_create_pty_201_response_deserializes_with_async_client():
    patch_settings()
    api_client = AsyncApiClient(ClientConfig(host="http://polyaxon").async_sdk_config)
    response = _Response(
        201,
        {
            "pty_id": "pty-1",
            "pid": 13,
            "state": "running",
            "started_at": "2026-01-01T00:00:00Z",
            "duration_ms": 0,
            "last_activity": "2026-01-01T00:00:00Z",
            "last_client_activity": "2026-01-01T00:00:00Z",
            "attached": False,
            "cols": 80,
            "rows": 24,
        },
    )

    with patch.object(api_client, "request", AsyncMock(return_value=response)):
        result = await SandboxV1Api(api_client).create_pty(
            namespace="ns",
            owner="owner",
            project="project",
            uuid="run-uuid",
            body=V1CreatePtyRequest(command=["sh"], cols=80, rows=24),
        )

    await api_client.close()
    assert isinstance(result, V1Pty)
    assert result.pty_id == "pty-1"
    assert result.duration_ms == 0
    assert result.cols == 80
