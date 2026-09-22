import copy
from typing import Dict, List

from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.params.params import V1Param
from polyaxon._polyaxonfile.specs.libs.parser import PolyaxonfileParser


def get_op_from_schedule(
    content: str,
    compiled_operation: V1CompiledOperation,
) -> V1Operation:
    op_spec = V1Operation.read(content)
    op_spec.conditions = None
    op_spec.schedule = None
    op_spec.events = None
    op_spec.dependencies = None
    op_spec.trigger = None
    op_spec.build = None
    op_spec.skip_on_upstream_skip = None
    op_spec.cache = compiled_operation.cache
    op_spec.queue = compiled_operation.queue
    op_spec.namespace = compiled_operation.namespace
    op_spec.strict_params = compiled_operation.strict_params
    op_spec.component.inputs = compiled_operation.inputs
    op_spec.component.outputs = compiled_operation.outputs
    op_spec.component.run = compiled_operation.run
    op_spec.component.strict_params = compiled_operation.strict_params
    return op_spec


def get_ops_from_suggestions(
    content: str,
    compiled_operation: V1CompiledOperation,
    suggestions: List[Dict],
) -> List[V1Operation]:
    op_content = V1Operation.read(content)  # TODO: Use construct

    def get_param(name: str, value) -> V1Param:
        source_param = (op_content.params or {}).get(name, V1Param())
        return V1Param(
            value=PolyaxonfileParser.parse_expression(value, {}),
            context_only=source_param.context_only,
            connection=source_param.connection,
            to_init=source_param.to_init,
            to_env=source_param.to_env,
        )

    for suggestion in suggestions:
        params = {k: get_param(k, v) for (k, v) in suggestion.items()}
        op_spec = copy.deepcopy(op_content)
        op_spec.matrix = None
        op_spec.conditions = None
        op_spec.schedule = None
        op_spec.events = None
        op_spec.dependencies = None
        op_spec.trigger = None
        op_spec.build = None
        op_spec.is_approved = None
        op_spec.skip_on_upstream_skip = None
        op_spec.cache = compiled_operation.cache
        op_spec.queue = compiled_operation.queue
        op_spec.namespace = compiled_operation.namespace
        op_spec.strict_params = compiled_operation.strict_params
        op_spec.params = params
        op_spec.component.inputs = compiled_operation.inputs
        op_spec.component.outputs = compiled_operation.outputs
        op_spec.component.run = compiled_operation.run
        op_spec.component.strict_params = compiled_operation.strict_params
        yield op_spec
