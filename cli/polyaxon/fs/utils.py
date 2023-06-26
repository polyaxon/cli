import os

from typing import Optional

from polyaxon.env_vars.keys import EV_KEYS_SANDBOX_IS_LOCAL
from polyaxon.lifecycle import V1ProjectFeature


def get_store_path(store_path: str, subpath: str, entity: Optional[str] = None) -> str:
    full_path = store_path

    if os.environ.get(EV_KEYS_SANDBOX_IS_LOCAL):
        dir_path = "runs" if entity == V1ProjectFeature.RUNTIME else f"{entity}s"
        full_path = os.path.join(full_path, dir_path)

    if subpath:
        full_path = os.path.join(full_path, subpath)
    return full_path
