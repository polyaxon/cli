from typing import List, Optional

from clipped.compact.pydantic import Field, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1Installation(BaseAllowSchemaModel):
    key: Optional[StrictStr]
    version: Optional[StrictStr]
    dist: Optional[StrictStr]
    host: Optional[StrictStr]
    hmac: Optional[StrictStr]
    mode: Optional[StrictStr]
    org: Optional[bool]
    single_url: Optional[bool] = Field(alias="singleUrl", default=None)
    default_streams_url: Optional[StrictStr] = Field(
        alias="defaultStreamsUrl", default=None
    )
    auth: Optional[List[StrictStr]]
