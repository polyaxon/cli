import uuid

from typing import Optional

from polyaxon._contexts.params import PARAM_REGEX, is_template_ref
from polyaxon.exceptions import PolyaxonValidationError

OPS = "ops"
RUNS = "runs"
DAG = "dag"
DAG_ENTITY_REF = "_"
ENTITIES = {OPS, RUNS}

ENTITY_REF_FORMAT = "{}.{}"


def is_runs_ref(ref: str) -> bool:
    return ref.split(".")[0] == RUNS


def is_ops_ref(ref: str) -> bool:
    return ref.split(".")[0] == OPS


def is_dag_ref(ref: str) -> bool:
    return ref.split(".")[0] == DAG


def get_entity_ref(ref: str) -> Optional[str]:
    if is_ops_ref(ref) or is_runs_ref(ref):
        return ref.split(".")[1]
    if is_dag_ref(ref):
        return DAG_ENTITY_REF
    return None


def get_entity_type(value: str) -> str:
    value_parts = PARAM_REGEX.search(value)
    if value_parts:
        results = value_parts.group(1).strip()
    else:
        results = value

    return results.split(".")[0]


def get_entity_value(value: str) -> Optional[str]:
    value_parts = PARAM_REGEX.search(value)
    if value_parts:
        results = value_parts.group(1).strip()
    else:
        results = value

    results = results.split(".")
    if len(results) < 2:
        return None
    return results[-1]


def parse_ref_value(value: str) -> str:
    """Returns value without {{ }}"""
    value_parts = PARAM_REGEX.search(value)
    if value_parts:
        return value_parts.group(1).strip()
    return value


class RefMixin:
    @property
    def is_literal(self) -> bool:
        return not self.ref  # type: ignore[attr-defined]

    @property
    def is_ref(self) -> bool:
        return self.ref is not None  # type: ignore[attr-defined]

    @property
    def is_template_ref(self) -> bool:
        return is_template_ref(self.value)

    @property
    def is_runs_ref(self) -> bool:
        if not self.is_ref:
            return False

        return is_runs_ref(self.ref)  # type: ignore[attr-defined]

    @property
    def is_ops_ref(self) -> bool:
        if not self.is_ref:
            return False

        return is_ops_ref(self.ref)  # type: ignore[attr-defined]

    @property
    def is_dag_ref(self) -> bool:
        if not self.is_ref:
            return False

        return is_dag_ref(self.ref)  # type: ignore[attr-defined]

    @property
    def is_join_ref(self):
        return False

    @property
    def entity_ref(self) -> Optional[str]:
        return get_entity_ref(self.ref)  # type: ignore[attr-defined]


def validate_ref(ref: str, name: str):
    # validate ref
    ref_parts = ref.split(".")
    if len(ref_parts) > 2:
        raise PolyaxonValidationError(
            "Could not parse ref `{}` for param `{}`.".format(ref, name)
        )
    if len(ref_parts) == 1 and ref_parts[0] != DAG:
        raise PolyaxonValidationError(
            "Could not parse ref `{}` for param `{}`.".format(ref_parts[0], name)
        )
    if len(ref_parts) == 2 and ref_parts[0] not in ENTITIES:
        raise PolyaxonValidationError(
            "Could not parse ref `{}` for param `{}`. "
            "Operation ref must be one of `{}`".format(ref_parts[0], name, ENTITIES)
        )
    if ref_parts[0] == RUNS:
        try:
            uuid.UUID(ref_parts[1])
        except (KeyError, ValueError):
            raise PolyaxonValidationError(
                "Param value `{}` should reference a valid run uuid.".format(
                    ref_parts[1]
                )
            )
