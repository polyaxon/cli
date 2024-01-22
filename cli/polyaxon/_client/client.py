from typing import TYPE_CHECKING, Optional

from polyaxon import settings
from polyaxon._constants.globals import NO_AUTH
from polyaxon._sdk.api import (
    AgentsV1Api,
    AuthV1Api,
    ConnectionsV1Api,
    DashboardsV1Api,
    OrganizationsV1Api,
    PresetsV1Api,
    ProjectDashboardsV1Api,
    ProjectSearchesV1Api,
    ProjectsV1Api,
    QueuesV1Api,
    RunsV1Api,
    SearchesV1Api,
    ServiceAccountsV1Api,
    TagsV1Api,
    TeamsV1Api,
    UsersV1Api,
    VersionsV1Api,
)
from polyaxon._sdk.async_client.api_client import AsyncApiClient
from polyaxon._sdk.sync_client.api_client import ApiClient

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
     * [RunClient](/docs/core/python-library/run-client/)
     * [ProjectClient](/docs/core/python-library/project-client/)
    """

    def __init__(
        self,
        config: Optional["ClientConfig"] = None,
        token: Optional[str] = None,
        is_async: bool = False,
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
        self.api_client = self._get_client()
        self._projects_v1 = None
        self._runs_v1 = None
        self._project_dashboards_v1 = None
        self._project_searches_v1 = None
        self._auth_v1 = None
        self._users_v1 = None
        self._versions_v1 = None
        self._agents_v1 = None
        self._internal_agents_v1 = None
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
        if self.is_async:
            return AsyncApiClient(
                self.config.async_sdk_config, **self.config.client_header
            )
        return ApiClient(self.config.sdk_config, **self.config.client_header)

    def _get_internal_client(self):
        if self.is_async:
            return AsyncApiClient(
                self.config.internal_sdk_config, **self.config.get_internal_header()
            )
        return ApiClient(
            self.config.internal_sdk_config, **self.config.get_internal_header()
        )

    def reset(self):
        self._projects_v1 = None
        self._runs_v1 = None
        self._project_dashboards_v1 = None
        self._project_searches_v1 = None
        self._auth_v1 = None
        self._users_v1 = None
        self._versions_v1 = None
        self._agents_v1 = None
        self._internal_agents_v1 = None
        self._queues_v1 = None
        self._service_accounts_v1 = None
        self._presets_v1 = None
        self._tags_v1 = None
        self._teams_v1 = None
        self._connections_v1 = None
        self._dashboards_v1 = None
        self._searches_v1 = None
        self._organizations_v1 = None
        self.api_client = self._get_client()

    @property
    def config(self):
        return self._config

    @property
    def projects_v1(self):
        if not self._projects_v1:
            self._projects_v1 = ProjectsV1Api(self.api_client)
        return self._projects_v1

    @property
    def runs_v1(self):
        if not self._runs_v1:
            self._runs_v1 = RunsV1Api(self.api_client)
        return self._runs_v1

    @property
    def auth_v1(self):
        if not self._auth_v1:
            self._auth_v1 = AuthV1Api(self.api_client)
        return self._auth_v1

    @property
    def users_v1(self):
        if not self._users_v1:
            self._users_v1 = UsersV1Api(self.api_client)
        return self._users_v1

    @property
    def versions_v1(self):
        if not self._versions_v1:
            self._versions_v1 = VersionsV1Api(self.api_client)
        return self._versions_v1

    @property
    def agents_v1(self):
        if not self._agents_v1:
            self._agents_v1 = AgentsV1Api(self.api_client)
        return self._agents_v1

    @property
    def internal_agents_v1(self):
        if not self._internal_agents_v1:
            self._internal_agents_v1 = AgentsV1Api(self._get_internal_client())
        return self._internal_agents_v1

    @property
    def queues_v1(self):
        if not self._queues_v1:
            self._queues_v1 = QueuesV1Api(self.api_client)
        return self._queues_v1

    @property
    def service_accounts_v1(self):
        if not self._service_accounts_v1:
            self._service_accounts_v1 = ServiceAccountsV1Api(self.api_client)
        return self._service_accounts_v1

    @property
    def tags_v1(self):
        if not self._tags_v1:
            self._tags_v1 = TagsV1Api(self.api_client)
        return self._tags_v1

    @property
    def teams_v1(self):
        if not self._teams_v1:
            self._teams_v1 = TeamsV1Api(self.api_client)
        return self._teams_v1

    @property
    def connections_v1(self):
        if not self._connections_v1:
            self._connections_v1 = ConnectionsV1Api(self.api_client)
        return self._connections_v1

    @property
    def project_dashboards_v1(self):
        if not self._project_dashboards_v1:
            self._project_dashboards_v1 = ProjectDashboardsV1Api(self.api_client)
        return self._project_dashboards_v1

    @property
    def project_searches_v1(self):
        if not self._project_searches_v1:
            self._project_searches_v1 = ProjectSearchesV1Api(self.api_client)
        return self._project_searches_v1

    @property
    def dashboards_v1(self):
        if not self._dashboards_v1:
            self._dashboards_v1 = DashboardsV1Api(self.api_client)
        return self._dashboards_v1

    @property
    def searches_v1(self):
        if not self._searches_v1:
            self._searches_v1 = SearchesV1Api(self.api_client)
        return self._searches_v1

    @property
    def presets_v1(self):
        if not self._presets_v1:
            self._presets_v1 = PresetsV1Api(self.api_client)
        return self._presets_v1

    @property
    def organizations_v1(self):
        if not self._organizations_v1:
            self._organizations_v1 = OrganizationsV1Api(self.api_client)
        return self._organizations_v1

    def sanitize_for_serialization(self, value):
        return self.api_client.sanitize_for_serialization(value)
