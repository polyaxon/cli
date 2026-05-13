from typing import Optional

from polyaxon import settings
from polyaxon._client.client import PolyaxonClient
from polyaxon._schemas.client import ClientConfig
from polyaxon._utils.fqn_utils import split_owner_team_space
from polyaxon.exceptions import PolyaxonClientException


class ClientMixin:
    _IS_ASYNC: bool = False

    def _raise_sync_only(self, method_name: str):
        raise PolyaxonClientException(
            "`{}` performs local file, stream, plotting, or artifact IO "
            "and is sync-only for now.".format(method_name)
        )

    def _set_client(self, client: Optional[PolyaxonClient]):
        if client is not None and client.is_async != self._IS_ASYNC:
            raise PolyaxonClientException(
                "Injected PolyaxonClient transport mode does not match client class."
            )
        self._client = client
        self._owns_client = client is None

    @property
    def client(self) -> PolyaxonClient:
        if getattr(self, "_client", None) is not None:
            return self._client
        self._client = PolyaxonClient(is_async=self._IS_ASYNC)
        self._owns_client = True
        return self._client

    def reset_client(self, **kwargs):
        if self._IS_ASYNC:
            raise PolyaxonClientException(
                "Use `await areset_client(...)` for async clients."
            )
        if not settings.CLIENT_CONFIG.in_cluster:
            previous = (
                self._client
                if getattr(self, "_owns_client", False)
                and getattr(self, "_client", None) is not None
                else None
            )
            self._client = PolyaxonClient(
                ClientConfig.patch_from(settings.CLIENT_CONFIG, **kwargs),
                is_async=False,
            )
            self._owns_client = True
            if previous is not None:
                previous.close()

    async def areset_client(self, **kwargs):
        if not self._IS_ASYNC:
            raise PolyaxonClientException("Use `reset_client(...)` for sync clients.")
        if not settings.CLIENT_CONFIG.in_cluster:
            previous = (
                self._client
                if getattr(self, "_owns_client", False)
                and getattr(self, "_client", None) is not None
                else None
            )
            self._client = PolyaxonClient(
                ClientConfig.patch_from(settings.CLIENT_CONFIG, **kwargs),
                is_async=True,
            )
            self._owns_client = True
            if previous is not None:
                await previous.aclose()

    async def _flush_on_exit(self) -> None:
        return None

    def __enter__(self):
        if self._IS_ASYNC:
            raise PolyaxonClientException("Use `async with` for async clients.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if getattr(self, "_owns_client", False) and getattr(self, "_client", None):
            self._client.close()

    async def __aenter__(self):
        if not self._IS_ASYNC:
            raise PolyaxonClientException("Use `with` for sync clients.")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            await self._flush_on_exit()
        finally:
            if getattr(self, "_owns_client", False) and getattr(self, "_client", None):
                await self._client.aclose()

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
