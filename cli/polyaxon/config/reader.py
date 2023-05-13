from clipped.config.reader import ConfigReader as _ConfigReader

from polyaxon.config.parser import ConfigParser
from polyaxon.config.spec import ConfigSpec


class ConfigReader(_ConfigReader):
    _CONFIG_SPEC = ConfigSpec
    _CONFIG_PARSER = ConfigParser
