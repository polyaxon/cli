from typing import Dict, Optional, Type

from clipped.utils.lists import to_list
from polyaxon._flow.io.io import V1IO
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.operations.operation import PartialV1Operation, V1Operation
from polyaxon._flow.params.params import V1Param
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile.specs import kinds
from polyaxon._polyaxonfile.specs.base import BaseSpecification
from polyaxon.exceptions import PolyaxonSchemaError


class OperationSpecification(BaseSpecification):
    """The polyaxonfile specification for operations."""

    _SPEC_KIND = kinds.OPERATION

    CONFIG: Type[V1Operation] = V1Operation
    PARTIAL_CONFIG: Type[PartialV1Operation] = PartialV1Operation

    @classmethod
    def compile_operation(
        cls,
        config: V1Polyaxonfile,
        override: Optional[Dict] = None,
        use_override_patch_strategy: bool = False,
    ) -> V1CompiledOperation:
        from polyaxon._polyaxonfile.manager.operations import compose_polyaxonfile

        preset_patch_strategy = None
        if override:
            preset = OperationSpecification.read(override, is_preset=True)
            if use_override_patch_strategy and preset.patch_strategy:
                preset_patch_strategy = preset.patch_strategy

            config = config.patch(preset, preset.patch_strategy)
        effective = compose_polyaxonfile(
            config, run_patch_strategy=preset_patch_strategy
        )
        if effective.run is None:
            raise PolyaxonSchemaError(
                "Compile operation received an invalid configuration: "
                "the resolved Polyaxonfile has no run."
            )

        contexts = []

        def get_context_io(c_name: str, c_io: V1Param, is_list=None):
            if not c_io.context_only:
                return

            contexts.append(
                V1IO.model_construct(
                    name=c_name,
                    to_init=c_io.to_init,
                    to_env=c_io.to_env,
                    connection=c_io.connection,
                    is_list=is_list,
                )
            )

        # Collect contexts IO from params.
        for p in effective.params or {}:
            get_context_io(c_name=p, c_io=effective.params[p])

        # Collect contexts IO from joins.
        for j in effective.joins or []:
            for p in j.params or {}:
                get_context_io(c_name=p, c_io=j.params[p], is_list=True)

        fields = effective.model_fields_set & set(
            V1CompiledOperation.get_model_fields()
        )
        values = {key: getattr(effective, key) for key in fields - {"kind"}}
        return V1CompiledOperation(
            kind=kinds.COMPILED_OPERATION, contexts=contexts, **values
        )

    @classmethod
    def read(cls, values, partial: bool = False, is_preset: bool = False):
        if is_preset:
            if isinstance(values, cls.CONFIG):
                values.is_preset = True
                return values
            elif isinstance(values, Dict):
                values[cls.IS_PRESET] = True
            else:
                values = to_list(values)
                values = [{cls.IS_PRESET: True}] + values

        return super().read(values, partial=partial or is_preset)
