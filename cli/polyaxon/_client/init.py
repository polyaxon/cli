from typing import Optional

from polyaxon import settings
from polyaxon._client.run import RunClient
from polyaxon.exceptions import PolyaxonClientException, PolyaxonContainerException


def get_client_or_raise() -> Optional[RunClient]:
    if settings.CLIENT_CONFIG.no_api:
        return None

    try:
        return RunClient()
    except PolyaxonClientException as e:
        raise PolyaxonContainerException(e)
