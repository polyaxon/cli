from typing import Optional

from polyaxon.schemas.api.version import V1Version
from polyaxon.schemas.base import BaseSchemaModel


class V1Compatibility(BaseSchemaModel):
    cli: Optional[V1Version]
    platform: Optional[V1Version]
    agent: Optional[V1Version]
    ui: Optional[V1Version]
