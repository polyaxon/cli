from typing import Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class ProxyConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    use_in_ops: Optional[bool] = Field(alias="useInOps", default=None)
    http_proxy: Optional[StrictStr] = Field(alias="httpProxy", default=None)
    https_proxy: Optional[StrictStr] = Field(alias="httpsProxy", default=None)
    no_proxy: Optional[StrictStr] = Field(alias="noProxy", default=None)
    port: Optional[StrictInt] = None
    host: Optional[StrictStr] = None
    protocol: Optional[StrictStr] = None
    kind: Optional[StrictStr] = None
