from typing import List, Optional

from clipped.compact.pydantic import Field, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1Installation(BaseAllowSchemaModel):
    key: Optional[StrictStr] = None
    version: Optional[StrictStr] = None
    dist: Optional[StrictStr] = None
    host: Optional[StrictStr] = None
    hmac: Optional[StrictStr] = None
    mode: Optional[StrictStr] = None
    org: Optional[bool] = None
    auth: Optional[List[StrictStr]] = None
    single_url: Optional[bool] = Field(alias="singleUrl", default=None)
    default_streams_url: Optional[StrictStr] = Field(
        alias="defaultStreamsUrl", default=None
    )
