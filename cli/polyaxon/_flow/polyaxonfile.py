from collections.abc import Mapping
from typing import Dict, List, Optional
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    StrictStr,
    field_validator,
    model_validator,
    validation_after,
    validation_before,
)
from clipped.config.patch_strategy import PatchStrategy
from clipped.config.schema import skip_partial, to_partial
from polyaxon._flow.io import V1IO
from polyaxon._flow.operations.base import BaseOp
from polyaxon._flow.params import V1Param, normalize_param_value
from polyaxon._flow.run.runtime import RunMixin, V1Runtime
from polyaxon._flow.templates import TemplateMixinConfig, V1Template


class V1Polyaxonfile(BaseOp, TemplateMixinConfig, RunMixin):
    """Internal authoring model; production readers still use the legacy models.

    Root fields may be omitted in reference and preset layers.
    Runtime-dependent validation, including runPatch, belongs after composition.
    """

    _CUSTOM_DUMP_FIELDS = {"run", "component", "termination"}

    kind: Optional[Literal["component", "operation"]] = None
    inputs: Optional[List[V1IO]] = None
    outputs: Optional[List[V1IO]] = None
    run: Optional[V1Runtime] = None
    template: Optional[V1Template] = None
    params: Optional[Dict[StrictStr, V1Param]] = None
    hub_ref: Optional[StrictStr] = Field(alias="hubRef", default=None)
    dag_ref: Optional[StrictStr] = Field(alias="dagRef", default=None)
    url_ref: Optional[StrictStr] = Field(alias="urlRef", default=None)
    path_ref: Optional[StrictStr] = Field(alias="pathRef", default=None)
    component: Optional["V1Polyaxonfile"] = None
    patch_strategy: Optional[PatchStrategy] = Field(alias="patchStrategy", default=None)
    is_preset: Optional[bool] = Field(alias="isPreset", default=None)
    run_patch: Optional[Dict] = Field(alias="runPatch", default=None)

    @field_validator("params", **validation_before)
    @classmethod
    def validate_params(cls, params):
        if not isinstance(params, Mapping):
            return params
        return {k: normalize_param_value(v) for k, v in params.items()}

    @model_validator(**validation_after)
    @skip_partial
    def validate_reference(cls, values):
        if not values or cls.get_value_for_key("is_preset", values):
            return values
        references = ("hub_ref", "dag_ref", "url_ref", "path_ref")
        if sum(bool(cls.get_value_for_key(ref, values)) for ref in references) > 1:
            raise ValueError(
                "At most one reference may be specified: "
                "hub_ref, dag_ref, url_ref, path_ref."
            )
        # Stored files can retain both a reference and its resolved component.
        return values

    def get_run_kind(self):
        return self.run.kind if self.run else None

    def get_replica_types(self):
        if self.is_distributed_run:
            return self.run.get_replica_types()


PartialV1Polyaxonfile = to_partial(V1Polyaxonfile)
