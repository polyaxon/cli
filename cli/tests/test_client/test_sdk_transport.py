from mock import MagicMock, patch
import pytest

from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.async_client.api_client import AsyncApiClient
from polyaxon._sdk.async_client.rest import RESTClientObject as AsyncRESTClientObject
from polyaxon._sdk.configuration import Configuration
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.sync_client.api_client import ApiClient
from polyaxon._sdk.sync_client.rest import RESTClientObject as SyncRESTClientObject
from polyaxon._utils.test_utils import AsyncMock, BaseTestCase
from polyaxon.exceptions import ApiValueError


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
