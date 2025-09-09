import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_settings_catalog import V1SettingsCatalog


class V1PresetSettings(BaseAllowSchemaModel):
    projects: Optional[List[V1SettingsCatalog]] = None
    runs: Optional[List[V1SettingsCatalog]] = None


class V1Preset(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr] = None
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    user: Optional[StrictStr] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    live_state: Optional[int] = None
    content: Optional[StrictStr] = None
    settings: Optional[V1PresetSettings] = None
