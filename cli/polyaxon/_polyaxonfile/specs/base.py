from collections.abc import Mapping
import copy

from clipped.utils.lists import to_list
from polyaxon._config.spec import ConfigSpec
from polyaxon._polyaxonfile.specs import kinds
from polyaxon._polyaxonfile.specs.sections import Sections
from polyaxon.exceptions import PolyaxonfileError, PolyaxonValidationError


class BaseSpecification(Sections):
    """Base abstract specification for plyaxonfiles and configurations."""

    _SPEC_KIND = None

    CONFIG = None
    PARTIAL_CONFIG = None

    @classmethod
    def check_kind(cls, data):
        if cls.KIND not in data:
            raise PolyaxonfileError("The Polyaxonfile `kind` must be specified.")

        if data[cls.KIND] not in kinds.KINDS:
            raise PolyaxonfileError(
                "The Polyaxonfile with kind `{}` is not a supported value.".format(
                    data[cls.KIND]
                )
            )

    @classmethod
    def check_data(cls, data):
        cls.check_kind(data)
        if data[cls.KIND] != cls._SPEC_KIND:
            raise PolyaxonfileError(
                "The specification used `{}` is incompatible with the kind `{}`.".format(
                    cls.__name__, data[cls.KIND]
                )
            )
        for key in set(data.keys()) - set(cls.SECTIONS):
            in_specification = "Polyaxonfile"
            if data.get(cls.VERSION):
                in_specification = "Polyaxonfile version `{}`".format(
                    data.get(cls.VERSION)
                )
            if data.get(cls.IS_PRESET):
                in_specification = "Polyaxonfile preset"

            raise PolyaxonfileError(
                "Unexpected section `{}` in {}. "
                "Please check the Polyaxonfile specification "
                "for this version.".format(key, in_specification)
            )

        for key in cls.REQUIRED_SECTIONS:
            if data.get(cls.IS_PRESET) and key == cls.VERSION:
                continue
            if key not in data:
                raise PolyaxonfileError(
                    "{} is a required section for a valid Polyaxonfile".format(key)
                )

    @classmethod
    def get_kind(cls, data):
        cls.check_kind(data=data)
        return data[cls.KIND]

    @classmethod
    def read(cls, values, partial: bool = False):
        if isinstance(values, cls.CONFIG):
            return values

        if not isinstance(values, Mapping) or Sections.KIND not in values:
            values = to_list(values)
            values = ConfigSpec.read_from([{Sections.KIND: cls._SPEC_KIND}] + values)
        cls.check_data(values)
        try:
            if partial and cls.PARTIAL_CONFIG:
                config = cls.PARTIAL_CONFIG.from_dict(
                    copy.deepcopy(values), partial=partial
                )
            else:
                config = cls.CONFIG.from_dict(copy.deepcopy(values), partial=partial)
        except TypeError as e:
            raise PolyaxonValidationError(
                "Received a non valid config `{}`: `{}`".format(cls._SPEC_KIND, e)
            )
        return config
