from typing import Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class ProxyConfig(BaseSchemaModel):
    enabled: Optional[bool]
    use_in_ops: Optional[bool] = Field(alias="useInOps")
    http_proxy: Optional[StrictStr] = Field(alias="httpProxy")
    https_proxy: Optional[StrictStr] = Field(alias="httpsProxy")
    no_proxy: Optional[StrictStr] = Field(alias="noProxy")
    port: Optional[StrictInt]
    host: Optional[StrictStr]
    protocol: Optional[StrictStr]
    kind: Optional[StrictStr]
