from typing import Any, Dict, List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.responses.v1_run_reference_catalog import V1RunReferenceCatalog
from polyaxon.schemas.responses.v1_settings_catalog import V1SettingsCatalog


class V1RunSettings(BaseSchemaModel):
    namespace: Optional[StrictStr]
    agent: Optional[V1SettingsCatalog]
    queue: Optional[V1SettingsCatalog]
    artifacts_store: Optional[V1SettingsCatalog]
    tensorboard: Optional[Dict[str, Any]]
    build: Optional[Dict[str, Any]]
    component: Optional[Dict[str, Any]]
    models: Optional[List[V1RunReferenceCatalog]]
    artifacts: Optional[List[V1RunReferenceCatalog]]
