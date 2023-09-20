from typing import Optional

from polyaxon._schemas.base import BaseSchemaModel


class RBACConfig(BaseSchemaModel):
    enabled: Optional[bool]
