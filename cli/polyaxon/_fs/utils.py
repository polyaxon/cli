import os

from typing import Optional

from polyaxon._env_vars.keys import ENV_KEYS_SERVICE_MODE
from polyaxon._schemas.lifecycle import V1ProjectFeature
from polyaxon._services import PolyaxonServices


def get_store_path(store_path: str, subpath: str, entity: Optional[str] = None) -> str:
    full_path = store_path

    if os.environ.get(ENV_KEYS_SERVICE_MODE) == PolyaxonServices.VIEWER:
        dir_path = "runs" if entity == V1ProjectFeature.RUNTIME else f"{entity}s"
        full_path = os.path.join(full_path, dir_path)

    if subpath:
        full_path = os.path.join(full_path, subpath)
    return full_path
