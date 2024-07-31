import datetime

from typing import List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel
from clipped.types.uuids import UUIDStr

from polyaxon._sdk.schemas.v1_settings_catalog import V1SettingsCatalog


class V1PresetSettings(BaseAllowSchemaModel):
    projects: Optional[List[V1SettingsCatalog]]
    runs: Optional[List[V1SettingsCatalog]]


class V1Preset(BaseAllowSchemaModel):
    uuid: Optional[UUIDStr]
    name: Optional[StrictStr]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    frozen: Optional[bool]
    live_state: Optional[int]
    content: Optional[StrictStr]
    settings: Optional[V1PresetSettings]
