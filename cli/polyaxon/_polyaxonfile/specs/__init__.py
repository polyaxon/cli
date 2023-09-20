from collections.abc import Mapping

from polyaxon._config.spec import ConfigSpec
from polyaxon._polyaxonfile.specs import kinds as spec_kinds
from polyaxon._polyaxonfile.specs.base import BaseSpecification
from polyaxon._polyaxonfile.specs.compiled_operation import (
    CompiledOperationSpecification,
)
from polyaxon._polyaxonfile.specs.component import ComponentSpecification
from polyaxon._polyaxonfile.specs.operation import OperationSpecification

SPECIFICATION_BY_KIND = {
    spec_kinds.OPERATION: OperationSpecification,
    spec_kinds.COMPILED_OPERATION: CompiledOperationSpecification,
    spec_kinds.COMPONENT: ComponentSpecification,
}


def get_specification(data):
    if not isinstance(data, Mapping):
        data = ConfigSpec.read_from(data)
    kind = BaseSpecification.get_kind(data=data)
    return SPECIFICATION_BY_KIND[kind].read(data)
