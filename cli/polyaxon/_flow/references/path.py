from typing_extensions import Literal

from clipped.compact.pydantic import StrictStr

from polyaxon._flow.references.mixin import RefMixin
from polyaxon._schemas.base import BaseSchemaModel


class V1PathRef(BaseSchemaModel, RefMixin):
    _IDENTIFIER = "path_ref"
    _USE_DISCRIMINATOR = True

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    path: StrictStr

    def get_kind_value(self):
        return self.path
