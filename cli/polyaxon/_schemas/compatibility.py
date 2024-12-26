from typing import Optional

from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._schemas.version import V1Version


class V1Compatibility(BaseSchemaModel):
    cli: Optional[V1Version] = None
    platform: Optional[V1Version] = None
    agent: Optional[V1Version] = None
    ui: Optional[V1Version] = None
