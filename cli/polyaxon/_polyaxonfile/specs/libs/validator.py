import copy

from polyaxon._flow import V1Environment
from polyaxon.exceptions import PolyaxonfileError


def validate(spec, data):
    """Validates the data and creates the config objects"""
    data = copy.deepcopy(data)
    validated_data = {}

    def validate_keys(section, config, section_data):
        extra_args = [
            key for key in section_data.keys() if key not in config.__fields__.keys()
        ]
        if extra_args:
            raise PolyaxonfileError(
                "Extra arguments passed for `{}`: {}".format(section, extra_args)
            )

    def add_validated_section(section, config):
        if data.get(section):
            section_data = data[section]
            validate_keys(section=section, config=config, section_data=section_data)
            validated_data[section] = config.from_dict(section_data)

    add_validated_section(spec.ENVIRONMENT, V1Environment)

    return validated_data
