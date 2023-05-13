from typing import Optional

from polyaxon.schemas.base import BaseSchemaModel


class RBACConfig(BaseSchemaModel):
    enabled: Optional[bool]
