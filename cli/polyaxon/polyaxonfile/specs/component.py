from typing import Type

from polyaxon.polyaxonfile.specs import kinds
from polyaxon.polyaxonfile.specs.base import BaseSpecification
from polyaxon.polyflow import V1Component


class ComponentSpecification(BaseSpecification):
    """The polyaxonfile specification for component."""

    _SPEC_KIND = kinds.COMPONENT

    CONFIG: Type[V1Component] = V1Component
