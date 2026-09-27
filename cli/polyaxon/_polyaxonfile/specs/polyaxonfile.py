from collections.abc import Mapping
from copy import deepcopy

from polyaxon._config.spec import ConfigSpec
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

        model = PartialV1Polyaxonfile if partial or is_preset else V1Polyaxonfile
        config = model.from_dict(deepcopy(values))
    if is_preset:
        config.is_preset = True
    return config
