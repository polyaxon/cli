import os

from typing import Optional

from polyaxon.lifecycle import V1ProjectFeature


def get_store_path(store_path: str, subpath: str, entity: Optional[str] = None) -> str:
    full_path = store_path
    if entity == V1ProjectFeature.RUNTIME:
        from polyaxon.services.values import PolyaxonServices

        if PolyaxonServices.is_sandbox():
            full_path = os.path.join(full_path, "runs")
    else:
        full_path = os.path.join(full_path, f"{entity}s")

    if subpath:
        full_path = os.path.join(full_path, subpath)
    return full_path
