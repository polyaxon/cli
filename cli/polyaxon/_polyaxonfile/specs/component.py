from typing import Type

from polyaxon._flow import V1Component
from polyaxon._polyaxonfile.specs import kinds
from polyaxon._polyaxonfile.specs.base import BaseSpecification


class ComponentSpecification(BaseSpecification):
    """The polyaxonfile specification for component."""

    _SPEC_KIND = kinds.COMPONENT

    CONFIG: Type[V1Component] = V1Component
