from mock import patch
import pytest
import tempfile

from polyaxon import settings
from polyaxon._client.client import PolyaxonClient
from polyaxon._constants.globals import NO_AUTH
from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.api import (
    AgentsV1Api,
    AuthV1Api,
    ProjectsV1Api,
    RunsV1Api,
    UsersV1Api,
    VersionsV1Api,
)
from polyaxon._utils.test_utils import BaseTestCase, patch_settings
from polyaxon.exceptions import PolyaxonClientException


class SDKClientMock:
    def __init__(self, name=None, events=None):
        self.name = name
        self.events = events
        self.close_calls = 0

    def close(self):
        self.close_calls += 1
        if self.events is not None:
            self.events.append("{}:close".format(self.name))


class AsyncSDKClientMock(SDKClientMock):
    async def close(self):
        self.close_calls += 1
        if self.events is not None:
            self.events.append("{}:close".format(self.name))


@pytest.mark.client_mark
class TestPolyaxonClient(BaseTestCase):
    def setUp(self):
        super().setUp()
        settings.CONTEXT_AUTH_TOKEN_PATH = "{}/{}".format(tempfile.mkdtemp(), ".auth")

    def test_client_services(self):
        settings.AUTH_CONFIG.token = None
        client = PolyaxonClient(token=None)
        assert client.is_internal is False
        assert client.config.token is None

        assert isinstance(client.config, ClientConfig)

        assert isinstance(client.auth_v1, AuthV1Api)
        assert isinstance(client.versions_v1, VersionsV1Api)
        assert isinstance(client.projects_v1, ProjectsV1Api)
        assert isinstance(client.runs_v1, RunsV1Api)
        assert isinstance(client.users_v1, UsersV1Api)

    def test_internal_client_services(self):
        client = PolyaxonClient(is_internal=True)
        assert client.is_internal is True
        assert isinstance(client.agents_v1, AgentsV1Api)

    def test_sync_internal_client_uses_internal_config(self):
        settings.CLIENT_CONFIG.token = "token"
        with patch("polyaxon._client.client.ApiClient") as api_client:
            PolyaxonClient(is_internal=True)

        sdk_config = api_client.call_args.args[0]
        assert sdk_config.api_key_prefix["ApiKey"] == "InternalToken"
        assert (
            api_client.call_args.kwargs == settings.CLIENT_CONFIG.get_internal_header()
        )

    def test_async_internal_client_uses_async_internal_config(self):
        settings.CLIENT_CONFIG.token = "token"
        with patch("polyaxon._client.client.AsyncApiClient") as api_client:
            PolyaxonClient(is_async=True, is_internal=True)

        sdk_config = api_client.call_args.args[0]
        assert sdk_config.api_key_prefix["ApiKey"] == "InternalToken"
        assert sdk_config.connection_pool_maxsize == 100
        assert (
            api_client.call_args.kwargs == settings.CLIENT_CONFIG.get_internal_header()
        )

    def test_from_config(self):
        settings.CLIENT_CONFIG.host = "localhost"
        client = PolyaxonClient(config=ClientConfig())
        assert client.config.is_managed is False
        assert client.config.host == "http://localhost:8000"
        assert client.config.token is None

    def test_from_settings(self):
        settings.CLIENT_CONFIG.is_managed = True
        settings.CLIENT_CONFIG.host = "api_host"
        client = PolyaxonClient(token="token")
        assert client.config.is_managed is True
        assert client.config.host == "api_host"
        assert client.config.token == "token"
        assert client.config.base_url == "api_host/api/v1"

    def test_load_token(self):
        settings.CLIENT_CONFIG.host = "localhost"
        client = PolyaxonClient(config=ClientConfig(token="test"))
        assert client.config.is_managed is False
        assert client.config.host == "http://localhost:8000"
        assert client.config.token == "test"

        client = PolyaxonClient(config=ClientConfig(token="test"), token="test2")
        assert client.config.is_managed is False
        assert client.config.host == "http://localhost:8000"
        assert client.config.token == "test2"

        client = PolyaxonClient(config=ClientConfig(token="test"), token=NO_AUTH)
        assert client.config.is_managed is False
        assert client.config.host == "http://localhost:8000"
        assert client.config.token is None

        client = PolyaxonClient(config=ClientConfig(token=NO_AUTH), token="test2")
        assert client.config.is_managed is False
        assert client.config.host == "http://localhost:8000"
        assert client.config.token == "test2"

    def test_close_raises_on_async_instance(self):
        sdk_client = AsyncSDKClientMock()
        with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
            client = PolyaxonClient(is_async=True)

        with pytest.raises(PolyaxonClientException):
            client.close()

    def test_reset_raises_on_async_instance(self):
        sdk_client = AsyncSDKClientMock()
        with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
            client = PolyaxonClient(is_async=True)

        with pytest.raises(PolyaxonClientException):
            client.reset()

    def test_close_calls_api_client_close(self):
        sdk_client = SDKClientMock()
        with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
            client = PolyaxonClient()
            client.close()

        assert sdk_client.close_calls == 1

    def test_reset_closes_previous_after_replacement(self):
        events = []
        previous = SDKClientMock(name="previous", events=events)
        replacement = SDKClientMock(name="replacement", events=events)

        def get_client(client):
            if not events:
                events.append("previous:make")
                return previous
            events.append("replacement:make")
            return replacement

        with patch.object(PolyaxonClient, "_get_client", autospec=True) as mock_get:
            mock_get.side_effect = get_client
            client = PolyaxonClient()
            client.reset()

        assert client.api_client is replacement
        assert events == ["previous:make", "replacement:make", "previous:close"]

    def test_supports_sync_context_manager(self):
        sdk_client = SDKClientMock()
        with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
            with PolyaxonClient() as client:
                assert client.api_client is sdk_client

        assert sdk_client.close_calls == 1

    def test_sync_context_manager_raises_on_async_instance(self):
        sdk_client = AsyncSDKClientMock()
        with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
            client = PolyaxonClient(is_async=True)

        with pytest.raises(PolyaxonClientException):
            with client:
                pass


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_aclose_raises_on_sync_instance():
    patch_settings()
    sdk_client = SDKClientMock()
    with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
        client = PolyaxonClient()

    with pytest.raises(PolyaxonClientException):
        await client.aclose()


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_areset_raises_on_sync_instance():
    patch_settings()
    sdk_client = SDKClientMock()
    with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
        client = PolyaxonClient()

    with pytest.raises(PolyaxonClientException):
        await client.areset()


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_aclose_awaits_api_client_close():
    patch_settings()
    sdk_client = AsyncSDKClientMock()
    with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
        client = PolyaxonClient(is_async=True)
        await client.aclose()

    assert sdk_client.close_calls == 1


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_areset_closes_previous_after_replacement():
    patch_settings()
    events = []
    previous = AsyncSDKClientMock(name="previous", events=events)
    replacement = AsyncSDKClientMock(name="replacement", events=events)

    def get_client(client):
        if not events:
            events.append("previous:make")
            return previous
        events.append("replacement:make")
        return replacement

    with patch.object(PolyaxonClient, "_get_client", autospec=True) as mock_get:
        mock_get.side_effect = get_client
        client = PolyaxonClient(is_async=True)
        await client.areset()

    assert client.api_client is replacement
    assert events == ["previous:make", "replacement:make", "previous:close"]


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_supports_async_context_manager():
    patch_settings()
    sdk_client = AsyncSDKClientMock()
    with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
        async with PolyaxonClient(is_async=True) as client:
            assert client.api_client is sdk_client

    assert sdk_client.close_calls == 1


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_context_manager_raises_on_sync_instance():
    patch_settings()
    sdk_client = SDKClientMock()
    with patch.object(PolyaxonClient, "_get_client", return_value=sdk_client):
        client = PolyaxonClient()

    with pytest.raises(PolyaxonClientException):
        async with client:
            pass
