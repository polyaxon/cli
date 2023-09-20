from typing import Dict, List, Optional

from clipped.compact.pydantic import Extra, Field, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class IngressConfig(BaseSchemaModel):
    enabled: Optional[bool]
    host_name: Optional[StrictStr] = Field(alias="hostName")
    path: Optional[StrictStr]
    tls: Optional[List[Dict]]
    annotations: Optional[Dict]

    class Config:
        extra = Extra.ignore
