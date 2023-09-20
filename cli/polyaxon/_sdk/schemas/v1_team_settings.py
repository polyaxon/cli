from typing import List, Optional

from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_settings_catalog import V1SettingsCatalog


class V1TeamSettings(BaseAllowSchemaModel):
    projects: Optional[List[V1SettingsCatalog]]
    hubs: Optional[List[V1SettingsCatalog]]
