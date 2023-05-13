from typing_extensions import Literal

from pydantic import StrictStr

from polyaxon.polyflow.references.mixin import RefMixin
from polyaxon.schemas.base import BaseSchemaModel


class V1DagRef(BaseSchemaModel, RefMixin):
    _IDENTIFIER = "dag_ref"
    _USE_DISCRIMINATOR = True

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    name: StrictStr

    def get_kind_value(self):
        return self.name
