from typing import TYPE_CHECKING, Optional

from polyaxon import settings
from polyaxon._constants.globals import NO_AUTH
from polyaxon._sdk.async_client.api_client import AsyncApiClient
from polyaxon._sdk.sync_client.api_client import ApiClient
from polyaxon.exceptions import PolyaxonClientException


if TYPE_CHECKING:
    from polyaxon._schemas.client import ClientConfig


class PolyaxonClient:
    """Auto-configurable and high-level base client that abstract
    the need to set a configuration for each service.

    PolyaxonClient comes with logic
    to pass config and token to other specific clients.

    If no values are passed to this class,
    Polyaxon will try to resolve the configuration from the environment:
     * If you have a configured CLI, Polyaxon will use the configuration of the cli.
     * If you use this client in the context of a job or a service managed by Polyaxon,
       a configuration will be available.

    Args:
        config: ClientConfig, optional, Instance of a ClientConfig.
        token: str, optional, the token to use for authenticating the clients,
               if the user is already logged in using the CLI, it will automatically use that token.
               Using the client inside a job/service scheduled with Polyaxon will have access to the
               token of the user who started the run if the `auth` context is enabled.

    You can access specific low level clients:

    ```python
    >>> client = PolyaxonClient()

    >>> client.projects_v1
    >>> client.runs_v1
    >>> client.auth_v1
    >>> client.users_v1
    >>> client.agents_v1
    >>> client.connections_v1
    >>> client.organizations_v1
    ```

    If you are interacting with a run or with a project, we suggest that you check:
     * [RunClient](/docs/references/python-library/run-client/)
     * [ProjectClient](/docs/references/python-library/project-client/)
    """

    def __init__(
        self,
        config: Optional["ClientConfig"] = None,
        token: Optional[str] = None,
        is_async: bool = False,
        is_internal: bool = False,
    ):
        self._config = config or settings.CLIENT_CONFIG
        token = token or self._config.token
        if not token and settings.AUTH_CONFIG:
            self._config.token = settings.AUTH_CONFIG.token
        elif token == NO_AUTH:
            self._config.token = None
        else:
            self._config.token = token

        self.is_async = is_async
        self.is_internal = is_internal
        self.api_client = self._get_client()
        self._reset_api_wrappers()

    def _reset_api_wrappers(self):
        self._projects_v1 = None
        self._runs_v1 = None
        self._sandbox_v1 = None
        self._project_dashboards_v1 = None
        self._project_searches_v1 = None
        self._auth_v1 = None
        self._users_v1 = None
        self._versions_v1 = None
        self._agents_v1 = None
        self._queues_v1 = None
        self._service_accounts_v1 = None
        self._presets_v1 = None
        self._tags_v1 = None
        self._teams_v1 = None
        self._connections_v1 = None
        self._dashboards_v1 = None
        self._searches_v1 = None
        self._organizations_v1 = None

    def _get_client(self):
        if self.is_internal:
            headers = self.config.get_internal_header()
            if self.is_async:
                return AsyncApiClient(self.config.async_internal_sdk_config, **headers)
            return ApiClient(self.config.internal_sdk_config, **headers)

        if self.is_async:
            return AsyncApiClient(
                self.config.async_sdk_config, **self.config.client_header
            )
        return ApiClient(self.config.sdk_config, **self.config.client_header)

    def reset(self):
        if self.is_async:
            raise PolyaxonClientException("Use `await areset()` for async clients.")
        previous_client = self.api_client
        self.api_client = self._get_client()
        self._reset_api_wrappers()
        previous_client.close()

    async def areset(self):
        if not self.is_async:
            raise PolyaxonClientException("Use `reset()` for sync clients.")
        previous_client = self.api_client
        self.api_client = self._get_client()
        self._reset_api_wrappers()
        await previous_client.close()

    def close(self):
        if self.is_async:
            raise PolyaxonClientException("Use `await aclose()` for async clients.")
        self.api_client.close()

    async def aclose(self):
        if not self.is_async:
            raise PolyaxonClientException("Use `close()` for sync clients.")
        await self.api_client.close()

    def __enter__(self):
        if self.is_async:
            raise PolyaxonClientException("Use `async with` for async clients.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    async def __aenter__(self):
        if not self.is_async:
            raise PolyaxonClientException("Use `with` for sync clients.")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.aclose()

    @property
    def config(self):
        return self._config

    @property
    def projects_v1(self):
        if not self._projects_v1:
            from polyaxon._sdk.api.projects_v1_api import ProjectsV1Api

            self._projects_v1 = ProjectsV1Api(self.api_client)
        return self._projects_v1

    @property
    def runs_v1(self):
        if not self._runs_v1:
            from polyaxon._sdk.api.runs_v1_api import RunsV1Api

            self._runs_v1 = RunsV1Api(self.api_client)
        return self._runs_v1

    @property
    def sandbox_v1(self):
        if not self._sandbox_v1:
            from polyaxon._sdk.api.sandbox_v1_api import SandboxV1Api

            self._sandbox_v1 = SandboxV1Api(self.api_client)
        return self._sandbox_v1

    @property
    def auth_v1(self):
        if not self._auth_v1:
            from polyaxon._sdk.api.auth_v1_api import AuthV1Api

            self._auth_v1 = AuthV1Api(self.api_client)
        return self._auth_v1

    @property
    def users_v1(self):
        if not self._users_v1:
            from polyaxon._sdk.api.users_v1_api import UsersV1Api

            self._users_v1 = UsersV1Api(self.api_client)
        return self._users_v1

    @property
    def versions_v1(self):
        if not self._versions_v1:
            from polyaxon._sdk.api.versions_v1_api import VersionsV1Api

            self._versions_v1 = VersionsV1Api(self.api_client)
        return self._versions_v1

    @property
    def agents_v1(self):
        if not self._agents_v1:
            from polyaxon._sdk.api.agents_v1_api import AgentsV1Api

            self._agents_v1 = AgentsV1Api(self.api_client)
        return self._agents_v1

    @property
    def queues_v1(self):
        if not self._queues_v1:
            from polyaxon._sdk.api.queues_v1_api import QueuesV1Api

            self._queues_v1 = QueuesV1Api(self.api_client)
        return self._queues_v1

    @property
    def service_accounts_v1(self):
        if not self._service_accounts_v1:
            from polyaxon._sdk.api.service_accounts_v1_api import ServiceAccountsV1Api

            self._service_accounts_v1 = ServiceAccountsV1Api(self.api_client)
        return self._service_accounts_v1

    @property
    def tags_v1(self):
        if not self._tags_v1:
            from polyaxon._sdk.api.tags_v1_api import TagsV1Api

            self._tags_v1 = TagsV1Api(self.api_client)
        return self._tags_v1

    @property
    def teams_v1(self):
        if not self._teams_v1:
            from polyaxon._sdk.api.teams_v1_api import TeamsV1Api

            self._teams_v1 = TeamsV1Api(self.api_client)
        return self._teams_v1

    @property
    def connections_v1(self):
        if not self._connections_v1:
            from polyaxon._sdk.api.connections_v1_api import ConnectionsV1Api

            self._connections_v1 = ConnectionsV1Api(self.api_client)
        return self._connections_v1

    @property
    def project_dashboards_v1(self):
        if not self._project_dashboards_v1:
            from polyaxon._sdk.api.project_dashboards_v1_api import (
                ProjectDashboardsV1Api,
            )

            self._project_dashboards_v1 = ProjectDashboardsV1Api(self.api_client)
        return self._project_dashboards_v1

    @property
    def project_searches_v1(self):
        if not self._project_searches_v1:
            from polyaxon._sdk.api.project_searches_v1_api import (
                ProjectSearchesV1Api,
            )

            self._project_searches_v1 = ProjectSearchesV1Api(self.api_client)
        return self._project_searches_v1

    @property
    def dashboards_v1(self):
        if not self._dashboards_v1:
            from polyaxon._sdk.api.dashboards_v1_api import DashboardsV1Api

            self._dashboards_v1 = DashboardsV1Api(self.api_client)
        return self._dashboards_v1

    @property
    def searches_v1(self):
        if not self._searches_v1:
            from polyaxon._sdk.api.searches_v1_api import SearchesV1Api

            self._searches_v1 = SearchesV1Api(self.api_client)
        return self._searches_v1

    @property
    def presets_v1(self):
        if not self._presets_v1:
            from polyaxon._sdk.api.presets_v1_api import PresetsV1Api

            self._presets_v1 = PresetsV1Api(self.api_client)
        return self._presets_v1

    @property
    def organizations_v1(self):
        if not self._organizations_v1:
            from polyaxon._sdk.api.organizations_v1_api import OrganizationsV1Api

            self._organizations_v1 = OrganizationsV1Api(self.api_client)
        return self._organizations_v1

    def sanitize_for_serialization(self, value):
        return self.api_client.sanitize_for_serialization(value)
