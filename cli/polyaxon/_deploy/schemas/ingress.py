from typing import Dict, List, Optional

from clipped.compact.pydantic import Field, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class IngressConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    host_name: Optional[StrictStr] = Field(alias="hostName", default=None)
    path: Optional[StrictStr] = None
    tls: Optional[List[Dict]] = None
    annotations: Optional[Dict] = None

    class Config:
        extra = "ignore"
