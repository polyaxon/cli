from clipped.config.parser import ConfigParser as _ConfigParser
from clipped.decorators.memoization import memoize

from polyaxon.exceptions import PolyaxonSchemaError


class ConfigParser(_ConfigParser):
    _SCHEMA_EXCEPTION = PolyaxonSchemaError

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
