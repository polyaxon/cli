import pytest
import tempfile

from polyaxon import settings
from polyaxon.client.client import PolyaxonClient
from polyaxon.constants.globals import NO_AUTH
from polyaxon.schemas.client import ClientConfig
from polyaxon.sdk.api import (
    AuthV1Api,
    ProjectsV1Api,
    RunsV1Api,
    UsersV1Api,
    VersionsV1Api,
)
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.client_mark
class TestPolyaxonClient(BaseTestCase):
    def setUp(self):
        super().setUp()
        settings.CONTEXT_AUTH_TOKEN_PATH = "{}/{}".format(tempfile.mkdtemp(), ".auth")

    def test_client_services(self):
        settings.AUTH_CONFIG.token = None
        client = PolyaxonClient(token=None)
        assert client.config.token is None

        assert isinstance(client.config, ClientConfig)

        assert isinstance(client.auth_v1, AuthV1Api)
        assert isinstance(client.versions_v1, VersionsV1Api)
        assert isinstance(client.projects_v1, ProjectsV1Api)
        assert isinstance(client.runs_v1, RunsV1Api)
        assert isinstance(client.users_v1, UsersV1Api)

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
