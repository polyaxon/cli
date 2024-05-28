from polyaxon import settings
from polyaxon._client.client import PolyaxonClient
from polyaxon._schemas.client import ClientConfig
from polyaxon._utils.fqn_utils import split_owner_team_space


class ClientMixin:
    @property
    def client(self):
        if self._client:
            return self._client
        self._client = PolyaxonClient()
        return self._client

    def reset_client(self, **kwargs):
        if not settings.CLIENT_CONFIG.in_cluster:
            self._client = PolyaxonClient(
                ClientConfig.patch_from(settings.CLIENT_CONFIG, **kwargs)
            )

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def team(self):
        return self._team

    @property
    def project(self) -> str:
        return self._project

    def set_project(self, project: str):
        self._project = project

    def set_owner(self, owner: str):
        owner, team = split_owner_team_space(owner)
        self._owner = owner
        self._team = team
