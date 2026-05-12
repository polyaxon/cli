import pytest

from mock import patch

from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.async_client.api_client import AsyncApiClient
from polyaxon._sdk.async_client.rest import RESTClientObject as AsyncRESTClientObject
from polyaxon._sdk.sync_client.api_client import ApiClient
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import ApiValueError


@pytest.mark.client_mark
class TestSDKTransport(BaseTestCase):
    def test_async_api_client_rejects_async_req(self):
        client = AsyncApiClient(ClientConfig(host="localhost").async_sdk_config)

        with pytest.raises(ApiValueError):
            client.call_api(
                resource_path="/api/v1/test",
                method="GET",
                async_req=True,
            )

    def test_async_rest_does_not_open_session_on_init(self):
        rest_client = AsyncRESTClientObject(ClientConfig(host="localhost").async_sdk_config)

        assert rest_client.pool_manager is None

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
