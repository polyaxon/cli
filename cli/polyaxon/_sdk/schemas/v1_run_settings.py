from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel

from polyaxon._sdk.schemas.v1_run_reference_catalog import V1RunReferenceCatalog
from polyaxon._sdk.schemas.v1_settings_catalog import V1SettingsCatalog


class V1RunSettings(BaseAllowSchemaModel):
    namespace: Optional[StrictStr] = None
    agent: Optional[V1SettingsCatalog] = None
    queue: Optional[V1SettingsCatalog] = None
    artifacts_store: Optional[V1SettingsCatalog] = None
    tensorboard: Optional[Dict[str, Any]] = None
    build: Optional[Dict[str, Any]] = None
    component: Optional[Dict[str, Any]] = None
    models: Optional[List[V1RunReferenceCatalog]] = None
    artifacts: Optional[List[V1RunReferenceCatalog]] = None
