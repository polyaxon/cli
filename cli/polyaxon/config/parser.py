from clipped.config.parser import ConfigParser as _ConfigParser
from clipped.decorators.memoization import memoize


class ConfigParser(_ConfigParser):
    @staticmethod
    @memoize
    def type_mapping():
        from polyaxon import types

        return types.MAPPING

    @staticmethod
    @memoize
    def type_forwarding():
        from polyaxon import types

        return types.FORWARDING
