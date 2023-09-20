from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_run_reference_catalog import V1RunReferenceCatalog
from polyaxon._sdk.schemas.v1_settings_catalog import V1SettingsCatalog


class V1RunSettings(BaseAllowSchemaModel):
    namespace: Optional[StrictStr]
    agent: Optional[V1SettingsCatalog]
    queue: Optional[V1SettingsCatalog]
    artifacts_store: Optional[V1SettingsCatalog]
    tensorboard: Optional[Dict[str, Any]]
    build: Optional[Dict[str, Any]]
    component: Optional[Dict[str, Any]]
    models: Optional[List[V1RunReferenceCatalog]]
    artifacts: Optional[List[V1RunReferenceCatalog]]
