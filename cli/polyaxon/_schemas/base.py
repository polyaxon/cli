from clipped.compact.pydantic import PYDANTIC_VERSION
from clipped.config.schema import BaseSchemaModel as _BaseSchemaModel
from clipped.config.schema import RootModel as _RootModel

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

    @property
    def _root(self):
        return self.__root__ if hasattr(self, "__root__") else self.root

    def set_root(self, value):
        if hasattr(self, "__root__"):
            self.__root__ = value
        else:
            self.root = value
        return self

    def get_root(self):
        return self._root

    @classmethod
    def make(cls, value):
        if PYDANTIC_VERSION.startswith("2."):
            return cls(root=value)
        return cls(__root__=value)
