from typing import List, Optional

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_settings_catalog import V1SettingsCatalog


class V1TeamSettings(BaseSchemaModel):
    projects: Optional[List[V1SettingsCatalog]]
    hubs: Optional[List[V1SettingsCatalog]]
