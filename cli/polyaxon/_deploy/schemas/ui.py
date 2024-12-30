from typing import Optional

from clipped.compact.pydantic import Field, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class UIConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    offline: Optional[bool] = None
    static_url: Optional[StrictStr] = Field(alias="staticUrl", default=None)
    base_url: Optional[StrictStr] = Field(alias="baseUrl", default=None)
    assets_version: Optional[StrictStr] = Field(alias="assetsVersion", default=None)
    admin_enabled: Optional[bool] = Field(alias="adminEnabled", default=None)
    single_url: Optional[bool] = Field(alias="singleUrl", default=None)
    default_streams_url: Optional[StrictStr] = Field(
        alias="defaultStreamsUrl", default=None
    )
