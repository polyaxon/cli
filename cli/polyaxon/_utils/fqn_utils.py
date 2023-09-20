import os
import re
import unicodedata

from typing import List, Optional, Tuple

from clipped.utils.paths import get_relative_path_to

from polyaxon.exceptions import PolyaxonSchemaError


def get_project_instance(owner: str, project: str) -> str:
    return "{}.{}".format(owner, project)


def get_run_instance(owner: str, project: str, run_uuid: str) -> str:
    return "{}.{}.runs.{}".format(owner, project, run_uuid)


def get_cleaner_instance(owner: str, project: str, run_uuid: str) -> str:
    return "{}.{}.cleaners.{}".format(owner, project, run_uuid)


def get_resource_name(run_uuid: str) -> str:
    return "plx-operation-{}".format(run_uuid)


def get_cleaner_resource_name(run_uuid: str) -> str:
    return "plx-cleaner-{}".format(run_uuid)


def get_resource_name_for_kind(run_uuid: str, run_kind: Optional[str] = None) -> str:
    if run_kind == "cleaner":
        return get_cleaner_resource_name(run_uuid)
    # Operation
    return get_resource_name(run_uuid)


def to_fqn_name(name: str) -> str:
    if not name:
        raise ValueError("A name is required to process events.")

    value = str(name)
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\\\/\.\s-]", "", value).strip()
    value = re.sub(r"[\\\/]+", "__", value)
    value = re.sub(r"[-\.\s]+", "-", value)
    return value


def get_entity_full_name(
    owner: Optional[str] = None, entity: Optional[str] = None
) -> str:
    if owner and entity:
        return "{}/{}".format(owner, entity)
    return entity


def get_entity_info(entity: str) -> Tuple[str, str]:
    if not entity:
        raise PolyaxonSchemaError(
            "Received an invalid entity reference: `{}`".format(entity)
        )

    parts = entity.replace(".", "/").split("/")
    if len(parts) > 2:
        raise PolyaxonSchemaError(
            "Received an invalid entity reference: `{}`".format(entity)
        )
    if len(parts) == 2:
        owner, entity_name = parts
    else:
        owner = None
        entity_name = entity

    return owner, entity_name


def get_versioned_entity_full_name(
    owner: Optional[str], component: str, tag: Optional[str] = None
) -> str:
    if tag:
        component = "{}:{}".format(component, tag)
    if owner:
        component = "{}/{}".format(owner, component)

    return component


def get_run_lineage_paths(run_uuid: str, lineage_paths: List[str]) -> List[str]:
    lineage_paths = [
        os.path.relpath(p, run_uuid) if run_uuid in p else p for p in lineage_paths
    ]
    return get_relative_path_to(run_uuid, lineage_paths)
