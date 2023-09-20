from typing import Dict, List, Optional
from typing_extensions import Literal

from polyaxon._flow.io import V1IO
from polyaxon._flow.operations.base import BaseOp
from polyaxon._flow.params import ParamSpec, ops_params
from polyaxon._flow.run import RunMixin, V1Runtime
from polyaxon.exceptions import PolyaxonSchemaError


class V1CompiledOperation(BaseOp, RunMixin):
    _IDENTIFIER = "compiled_operation"

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    inputs: Optional[List[V1IO]]
    outputs: Optional[List[V1IO]]
    contexts: Optional[List[V1IO]]
    run: V1Runtime

    def get_run_kind(self):
        return self.run.kind if self.run else None

    def validate_params(
        self,
        params: Optional[Dict] = None,
        context: Optional[Dict] = None,
        is_template: bool = True,
        check_all_refs: bool = False,
        parse_values: bool = False,
        parse_joins: bool = True,
    ) -> List[ParamSpec]:
        return ops_params.validate_params(
            inputs=self.inputs,
            outputs=self.outputs,
            contexts=self.contexts,
            params=params,
            matrix=self.matrix,
            joins=self.joins if parse_joins else None,
            context=context,
            is_template=is_template,
            check_all_refs=check_all_refs,
            parse_values=parse_values,
        )

    def apply_params(self, params=None, context=None):
        context = context or {}
        validated_params = self.validate_params(
            params=params,
            context=context,
            is_template=False,
            check_all_refs=True,
            parse_values=True,
        )
        if not validated_params:
            return

        param_specs = {}
        for param in validated_params:
            param_specs[param.name] = param

        processed_params = set([])

        def set_io(io):
            if not io:
                return
            for i in io:
                if i.name in param_specs:
                    processed_params.add(i.name)
                    i.is_optional = True
                    if param_specs[i.name].param.is_literal:
                        current_param = param_specs[i.name].param
                        value = current_param.value
                        if hasattr(value, "to_param"):
                            value = value.to_param()
                        i.value = value
                        if current_param.connection:
                            i.connection = current_param.connection
                        if current_param.to_init:
                            i.to_init = current_param.to_init
                        if current_param.to_env:
                            i.to_env = current_param.to_env

        def set_contexts() -> List[V1IO]:
            context_params = [p for p in param_specs if p not in processed_params]
            contexts = []
            for p in context_params:
                current_param = param_specs[p].param
                contexts.append(
                    V1IO.construct(
                        name=p,
                        value=current_param.value,
                        is_optional=True,
                        connection=current_param.connection,
                        to_init=current_param.to_init,
                        to_env=current_param.to_env,
                    )
                )

            return contexts

        set_io(self.inputs)
        set_io(self.outputs)
        self.contexts = set_contexts()

    def get_env_io(self) -> List[List]:
        def get_env_io(io: List[V1IO]) -> List[List]:
            return [[i.to_env, i.value] for i in io if i.to_env]

        return (
            get_env_io(self.inputs or [])
            + get_env_io(self.outputs or [])
            + get_env_io(self.contexts or [])
        )

    def get_io_names(self) -> List[str]:
        def get_io_name(io: List[V1IO]) -> List[str]:
            return [i.name for i in io if i.name]

        return (
            get_io_name(self.inputs or [])
            + get_io_name(self.outputs or [])
            + get_io_name(self.contexts or [])
        )

    def apply_image_destination(self, image: str):
        self.run.apply_image_destination(image)

    @property
    def has_pipeline(self):
        return self.is_dag_run or self.matrix or self.schedule

    def validate_build(self):
        if self.build and self.is_dag_run:
            raise PolyaxonSchemaError(
                "Operations with dag runtime do not support the `build` section."
            )
