import os

from requests import HTTPError

from clipped.config.spec import ConfigSpec as _ConfigSpec

from polyaxon.env_vars.keys import ENV_KEYS_PUBLIC_REGISTRY, ENV_KEYS_USE_GIT_REGISTRY
from polyaxon.exceptions import (
    ApiException,
    PolyaxonClientException,
    PolyaxonSchemaError,
)


class ConfigSpec(_ConfigSpec):
    _SCHEMA_EXCEPTION = PolyaxonSchemaError

    @classmethod
    def get_public_registry(cls):
        if os.environ.get(ENV_KEYS_USE_GIT_REGISTRY, False):
            return os.environ.get(
                ENV_KEYS_PUBLIC_REGISTRY,
                "https://raw.githubusercontent.com/polyaxon/polyaxon-hub/master",
            )

    @classmethod
    def read_from_custom_hub(cls, hub: str):
        from polyaxon.client import PolyaxonClient, ProjectClient
        from polyaxon.constants.globals import DEFAULT_HUB, NO_AUTH
        from polyaxon.env_vars.getters import get_component_info
        from polyaxon.lifecycle import V1ProjectVersionKind
        from polyaxon.schemas.client import ClientConfig

        owner, component, version = get_component_info(hub)

        try:
            if owner == DEFAULT_HUB:
                client = PolyaxonClient(
                    config=ClientConfig(use_cloud_host=True, verify_ssl=False),
                    token=NO_AUTH,
                )
            else:
                client = PolyaxonClient()
            project_client = ProjectClient(
                owner=owner, project=component, client=client
            )
            response = project_client.get_version(
                kind=V1ProjectVersionKind.COMPONENT, version=version
            )
            return cls.read_from_stream(response.content)
        except (ApiException, HTTPError) as e:
            raise PolyaxonClientException(
                "Component `{}` could not be fetched, "
                "an error was encountered {}".format(hub, e)
            )
