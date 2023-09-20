from typing import Optional

from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._schemas.version import V1Version


class V1Compatibility(BaseSchemaModel):
    cli: Optional[V1Version]
    platform: Optional[V1Version]
    agent: Optional[V1Version]
    ui: Optional[V1Version]
