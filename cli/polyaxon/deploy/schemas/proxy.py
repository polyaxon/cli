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

from typing import Optional

from pydantic import Field, StrictInt, StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class ProxyConfig(BaseSchemaModel):
    enabled: Optional[bool]
    use_in_ops: Optional[bool] = Field(alias="useInOps")
    http_proxy: Optional[StrictStr] = Field(alias="httpProxy")
    https_proxy: Optional[StrictStr] = Field(alias="httpsProxy")
    no_proxy: Optional[StrictStr] = Field(alias="noProxy")
    port: Optional[StrictInt]
    host: Optional[StrictStr]
    kind: Optional[StrictStr]
