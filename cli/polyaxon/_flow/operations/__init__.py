from clipped.compact.pydantic import model_rebuild

from polyaxon._flow.component.component import V1Component
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.run.dag import V1Dag


# Forward references for operations and components
model_rebuild(V1Dag, V1Operation=V1Operation, V1Component=V1Component)
