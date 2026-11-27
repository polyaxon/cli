from clipped.config.schema import (
    BaseSchemaModel as _BaseSchemaModel,
    RootModel as _RootModel,
)
from polyaxon import pkg
from polyaxon._config.spec import ConfigSpec
from polyaxon.exceptions import PolyaxonSchemaError


class BaseSchemaModel(_BaseSchemaModel):
    _VERSION = pkg.SCHEMA_VERSION
    _SCHEMA_EXCEPTION = PolyaxonSchemaError
    _CONFIG_SPEC = ConfigSpec


class RootModel(_RootModel):
    _VERSION = pkg.SCHEMA_VERSION
    _SCHEMA_EXCEPTION = PolyaxonSchemaError
    _CONFIG_SPEC = ConfigSpec

    def set_root(self, value):
        self.root = value
        return self

    def get_root(self):
        return self.root

    @classmethod
    def make(cls, value):
        return cls(root=value)
