from collections.abc import Mapping
from copy import deepcopy

from polyaxon._config.spec import ConfigSpec
from polyaxon._flow.component.component import V1Component
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.polyaxonfile import PartialV1Polyaxonfile, V1Polyaxonfile
from polyaxon.exceptions import PolyaxonfileError


def read_polyaxonfile(
    values, partial: bool = False, is_preset: bool = False
) -> V1Polyaxonfile:
    """Read one authored document without resolving references or merging layers."""
    if isinstance(values, V1Polyaxonfile):
        config = deepcopy(values)
    else:
        source = ConfigSpec.get_from(values)
        source.check_type()
        values = source.read()
        if not isinstance(values, Mapping):
            raise PolyaxonfileError("The Polyaxonfile must contain a mapping.")

        model = {
            "component": V1Component,
            "operation": V1Operation,
        }.get(values.get("kind"), V1Polyaxonfile)
        if partial or is_preset:
            model = PartialV1Polyaxonfile
        config = model.from_dict(deepcopy(values))
    if is_preset:
        config.is_preset = True
    return config
