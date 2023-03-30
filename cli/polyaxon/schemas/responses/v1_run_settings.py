#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
