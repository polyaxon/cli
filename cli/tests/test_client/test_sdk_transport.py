from mock import MagicMock, patch
import pytest

from polyaxon._cli.errors import handle_cli_error
from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.async_client.api_client import AsyncApiClient
from polyaxon._sdk.async_client.rest import RESTClientObject as AsyncRESTClientObject
from polyaxon._sdk.configuration import Configuration
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.sync_client.api_client import ApiClient
from polyaxon._sdk.sync_client.rest import RESTClientObject as SyncRESTClientObject
from polyaxon._utils.test_utils import AsyncMock, BaseTestCase
from polyaxon.exceptions import (
    ApiException,
    ApiValueError,
    ForbiddenException,
    NotFoundException,
    ServiceException,
)


async def get_async_request_timeout(configuration, request_timeout=None):
    rest_client = AsyncRESTClientObject(configuration)
    pool_manager = MagicMock()
    pool_manager.request = AsyncMock(return_value=MagicMock())
    with patch.object(rest_client, "_get_pool_manager", return_value=pool_manager):
        await rest_client.request(
            method="GET",
            url="http://localhost",
            _preload_content=False,
            _request_timeout=request_timeout,
        )
    return pool_manager.request.call_args.kwargs["timeout"]


def get_sync_request_timeout(configuration, request_timeout=None):
    rest_client = SyncRESTClientObject(configuration)
    pool_manager = MagicMock()
    pool_manager.request.return_value = MagicMock(status=200)
    rest_client.pool_manager = pool_manager
    rest_client.request(
        method="GET",
        url="http://localhost",
        _preload_content=False,
        _request_timeout=request_timeout,
    )
    return pool_manager.request.call_args.kwargs["timeout"]


@pytest.mark.client_mark
class TestSDKTransport(BaseTestCase):
    def test_list_runs_response_accepts_schedule_pipeline_kind(self):
        response = V1ListRunsResponse.from_dict(
            {"results": [{"pipeline": {"kind": "schedule"}}]}
        )

        assert response.results[0].pipeline.kind == "schedule"

    def test_async_api_client_rejects_async_req(self):
        client = AsyncApiClient(ClientConfig(host="localhost").async_sdk_config)

        with pytest.raises(ApiValueError):
            client.call_api(
                resource_path="/api/v1/test",
                method="GET",
                async_req=True,
            )

    def test_async_rest_does_not_open_session_on_init(self):
        rest_client = AsyncRESTClientObject(
            ClientConfig(host="localhost").async_sdk_config
        )

        assert rest_client.pool_manager is None

    def test_sync_rest_uses_configured_timeout(self):
        configuration = ClientConfig(host="localhost", timeout=17).sdk_config

        timeout = get_sync_request_timeout(configuration)

        assert timeout.total == 17

    def test_sync_rest_request_timeout_overrides_config(self):
        configuration = ClientConfig(host="localhost", timeout=17).sdk_config

        timeout = get_sync_request_timeout(configuration, request_timeout=3)

        assert timeout.total == 3

    def test_sync_rest_uses_no_timeout_without_configured_timeout(self):
        configuration = Configuration(timeout=None)

        assert get_sync_request_timeout(configuration) is None

    def test_sync_rest_keeps_connect_and_read_timeout_support(self):
        configuration = Configuration(timeout=None)

        timeout = get_sync_request_timeout(configuration, request_timeout=(2, 4))

        assert timeout.connect_timeout == 2
        assert timeout.read_timeout == 4

    def test_sync_api_client_close_calls_rest_close(self):
        client = ApiClient(ClientConfig(host="localhost").sdk_config)

        with patch.object(client.rest_client, "close") as rest_close:
            client.close()

        assert rest_close.call_count == 1

    def test_sync_rest_close_clears_pool_manager(self):
        client = ApiClient(ClientConfig(host="localhost").sdk_config)

        with patch.object(client.rest_client.pool_manager, "clear") as clear:
            client.rest_client.close()

        assert clear.call_count == 1

    def test_sync_api_client_query_bools_are_lowercase(self):
        client = ApiClient(ClientConfig(host="localhost").sdk_config)

        assert (
            client.parameters_to_url_query(
                {"enabled": True, "recursive": False, "limit": 3},
                collection_formats=None,
            )
            == "enabled=true&recursive=false&limit=3"
        )

    def test_async_api_client_query_bools_are_lowercase(self):
        client = AsyncApiClient(ClientConfig(host="localhost").async_sdk_config)

        assert (
            client.parameters_to_url_query(
                {"enabled": True, "recursive": False, "limit": 3},
                collection_formats=None,
            )
            == "enabled=true&recursive=false&limit=3"
        )


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_rest_uses_configured_timeout():
    configuration = ClientConfig(host="localhost", timeout=17).async_sdk_config

    assert configuration.timeout == 17
    assert await get_async_request_timeout(configuration) == 17


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_rest_request_timeout_overrides_config():
    configuration = ClientConfig(host="localhost", timeout=17).async_sdk_config

    assert await get_async_request_timeout(configuration, request_timeout=3) == 3


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_rest_uses_no_timeout_without_configured_timeout():
    configuration = Configuration(timeout=None)

    assert await get_async_request_timeout(configuration) is None


@pytest.mark.client_mark
@pytest.mark.parametrize(
    "status,error_type",
    [
        (403, ForbiddenException),
        (404, NotFoundException),
        (500, ServiceException),
        (599, ServiceException),
    ],
)
def test_sync_api_error_preserves_exception_and_adds_request_context(
    status, error_type
):
    client = ApiClient(ClientConfig(host="localhost").sdk_config)
    error = error_type(status=status, reason="Request failed")
    error.body = b'{"detail":"Request failed"}'
    error.headers = {"X-Request-ID": "request-id"}

    with patch.object(client, "request", side_effect=error):
        with pytest.raises(error_type) as raised:
            client.call_api(
                resource_path="/api/v1/{owner}/{entity}/versions/{kind}/{name}",
                method="GET",
                path_params={
                    "owner": "my org",
                    "entity": "my/project",
                    "kind": "component",
                    "name": "latest",
                },
                query_params={"token": "query-secret"},
                header_params={"Authorization": "Bearer header-secret"},
                _host="https://user:host-secret@private.example",
            )

    assert raised.value is error
    assert error.status == status
    assert error.reason == "Request failed"
    assert error.body == '{"detail":"Request failed"}'
    assert error.headers == {"X-Request-ID": "request-id"}
    context = "GET /api/v1/my%20org/my%2Fproject/versions/component/latest"
    assert error.request_context == context
    assert "HTTP request: {}\n".format(context) in str(error)
    assert "secret" not in str(error)
    assert "private.example" not in str(error)


@pytest.mark.client_mark
@pytest.mark.asyncio
@pytest.mark.parametrize("status", [403, 404, 500, 599])
async def test_async_api_error_preserves_exception_and_adds_request_context(status):
    client = AsyncApiClient(ClientConfig(host="localhost").async_sdk_config)
    error = ApiException(status=status, reason="Request failed")
    error.body = b'{"detail":"Request failed"}'
    error.headers = {"X-Request-ID": "request-id"}

    with patch.object(client, "request", new=AsyncMock(side_effect=error)):
        with pytest.raises(ApiException) as raised:
            await client.call_api(
                resource_path="/api/v1/{owner}/{project}/runs",
                method="POST",
                path_params={"owner": "my org", "project": "my/project"},
                query_params={"token": "query-secret"},
                header_params={"Authorization": "Bearer header-secret"},
                body={"password": "body-secret"},
                _host="https://user:host-secret@private.example",
            )

    assert raised.value is error
    assert error.status == status
    assert error.reason == "Request failed"
    assert error.body == '{"detail":"Request failed"}'
    assert error.headers == {"X-Request-ID": "request-id"}
    assert error.request_context == "POST /api/v1/my%20org/my%2Fproject/runs"
    assert "HTTP request: POST /api/v1/my%20org/my%2Fproject/runs\n" in str(error)
    assert "secret" not in str(error)
    assert "private.example" not in str(error)


@pytest.mark.client_mark
def test_api_exception_without_request_context_keeps_existing_format():
    error = ApiException(403, "Forbidden")
    error.headers = {"X-Request-ID": "request-id"}
    error.body = "Request failed"

    assert error.request_context is None
    assert str(error) == (
        "(403)\nReason: Forbidden\n"
        "HTTP response headers: {'X-Request-ID': 'request-id'}\n"
        "HTTP response body: Request failed\n"
    )


@pytest.mark.client_mark
@pytest.mark.parametrize("status", [403, 404, 500, 599])
@pytest.mark.parametrize("with_context", [False, True])
def test_cli_api_error_displays_request_context_once(status, with_context, capsys):
    error = ApiException(status=status, reason="Request failed")
    error.body = "Response detail"
    if with_context:
        error.set_request_context("GET", "/api/v1/test")

    handle_cli_error(error)

    output = capsys.readouterr().out
    assert output.count("HTTP request: GET /api/v1/test") == int(with_context)
    assert "Reason: Request failed" in output
    if status == 404:
        assert "Response detail" not in output
    else:
        assert "Response detail" in output
