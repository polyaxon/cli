import pytest
import tempfile

from mock import patch

from polyaxon import settings
from polyaxon._client.client import PolyaxonClient
from polyaxon._constants.globals import NO_AUTH
from polyaxon._schemas.client import ClientConfig
from polyaxon._sdk.api import (
    AuthV1Api,
    ProjectsV1Api,
    RunsV1Api,
    UsersV1Api,
    VersionsV1Api, AgentsV1Api,
)
from polyaxon._utils.test_utils import BaseTestCase


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
            api_client.call_args.kwargs
            == settings.CLIENT_CONFIG.get_internal_header()
        )

    def test_async_internal_client_uses_async_internal_config(self):
        settings.CLIENT_CONFIG.token = "token"
        with patch("polyaxon._client.client.AsyncApiClient") as api_client:
            PolyaxonClient(is_async=True, is_internal=True)

        sdk_config = api_client.call_args.args[0]
        assert sdk_config.api_key_prefix["ApiKey"] == "InternalToken"
        assert sdk_config.connection_pool_maxsize == 100
        assert (
            api_client.call_args.kwargs
            == settings.CLIENT_CONFIG.get_internal_header()
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
