from clipped.config.schema import BaseSchemaModel as _BaseSchemaModel

from polyaxon import pkg
from polyaxon._config.spec import ConfigSpec
from polyaxon.exceptions import PolyaxonSchemaError


class BaseSchemaModel(_BaseSchemaModel):
    _VERSION = pkg.SCHEMA_VERSION
    _SCHEMA_EXCEPTION = PolyaxonSchemaError
    _CONFIG_SPEC = ConfigSpec


NAME_REGEX = r"^[-a-zA-Z0-9_]+\Z"
FULLY_QUALIFIED_NAME_REGEX = r"^[-a-zA-Z0-9_]+(:[-a-zA-Z0-9_.]+)?\Z"
