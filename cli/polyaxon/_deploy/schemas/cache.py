from typing import Optional

from polyaxon._schemas.base import BaseSchemaModel


class CacheConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
