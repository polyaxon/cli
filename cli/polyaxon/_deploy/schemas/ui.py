from typing import Optional

from clipped.compact.pydantic import Field, StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class UIConfig(BaseSchemaModel):
    enabled: Optional[bool]
    offline: Optional[bool]
    static_url: Optional[StrictStr] = Field(alias="staticUrl")
    base_url: Optional[StrictStr] = Field(alias="baseUrl")
    assets_version: Optional[StrictStr] = Field(alias="assetsVersion")
    admin_enabled: Optional[bool] = Field(alias="adminEnabled")
