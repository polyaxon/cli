import copy

from typing import Dict, List

from polyaxon._flow import V1CompiledOperation, V1Operation, V1Param
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
    op_spec.component.inputs = compiled_operation.inputs
    op_spec.component.outputs = compiled_operation.outputs
    op_spec.component.run = compiled_operation.run
    return op_spec


def get_ops_from_suggestions(
    content: str,
    compiled_operation: V1CompiledOperation,
    suggestions: List[Dict],
) -> List[V1Operation]:
    io_keys = compiled_operation.get_io_names()

    def has_param(k: str):
        if not compiled_operation.matrix:
            return None
        return k not in io_keys

    op_content = V1Operation.read(content)  # TODO: Use construct
    for suggestion in suggestions:
        params = {
            k: V1Param(
                value=PolyaxonfileParser.parse_expression(v, {}),
                context_only=has_param(k),
            )
            for (k, v) in suggestion.items()
        }
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
        op_spec.params = params
        op_spec.component.inputs = compiled_operation.inputs
        op_spec.component.outputs = compiled_operation.outputs
        op_spec.component.run = compiled_operation.run
        yield op_spec
