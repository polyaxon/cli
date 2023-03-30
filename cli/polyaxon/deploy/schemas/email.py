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


class EmailConfig(BaseSchemaModel):
    enabled: Optional[bool]
    email_from: Optional[StrictStr] = Field(alias="from")
    host: Optional[StrictStr]
    port: Optional[StrictInt]
    use_tls: Optional[bool] = Field(alias="useTls")
    host_user: Optional[StrictStr] = Field(alias="hostUser")
    host_password: Optional[StrictStr] = Field(alias="hostPassword")
    backend: Optional[StrictStr]
