import copy
from typing import Dict, List

from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.params.params import V1Param
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile.manager.operations import compose_polyaxonfile
from polyaxon._polyaxonfile.specs.libs.parser import PolyaxonfileParser
from polyaxon._polyaxonfile.specs.polyaxonfile import read_polyaxonfile


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
) -> List[V1Polyaxonfile]:
    op_content = read_polyaxonfile(content)
    source_params = compose_polyaxonfile(op_content).params or {}

    def get_param(name: str, value) -> V1Param:
        source_param = source_params.get(name, V1Param())
        return V1Param(
            value=PolyaxonfileParser.parse_expression(value, {}),
            context_only=source_param.context_only,
            connection=source_param.connection,
            to_init=source_param.to_init,
            to_env=source_param.to_env,
        )

    # Clear every source layer so inherited fields cannot become active again.
    layer = op_content
    while layer is not None:
        for field in (
            "matrix",
            "conditions",
            "schedule",
            "events",
            "dependencies",
            "trigger",
            "build",
            "is_approved",
            "skip_on_upstream_skip",
            "params",
            "inputs",
            "outputs",
            "run",
            "run_patch",
            "cache",
            "queue",
            "namespace",
            "strict_params",
        ):
            setattr(layer, field, None)
            layer.model_fields_set.discard(field)
        layer = layer.component

    op_content.cache = copy.deepcopy(compiled_operation.cache)
    op_content.queue = compiled_operation.queue
    op_content.namespace = compiled_operation.namespace
    op_content.strict_params = compiled_operation.strict_params
    component = op_content.component or op_content
    component.inputs = copy.deepcopy(compiled_operation.inputs)
    component.outputs = copy.deepcopy(compiled_operation.outputs)
    component.run = copy.deepcopy(compiled_operation.run)
    component.strict_params = compiled_operation.strict_params

    # Declared values are already in inputs/outputs; contexts need child params.
    op_content.params = {
        io.name: V1Param(
            value=copy.deepcopy(io.value),
            context_only=source_params.get(
                io.name, V1Param(context_only=True)
            ).context_only,
            connection=io.connection,
            to_init=io.to_init,
            to_env=io.to_env,
        )
        for io in compiled_operation.contexts or []
    }
    for suggestion in suggestions:
        op_spec = copy.deepcopy(op_content)
        op_spec.params.update({k: get_param(k, v) for (k, v) in suggestion.items()})
        yield op_spec
