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
from typing import List, Optional, Union

from pydantic import Field, StrictStr, constr, validator

from polyaxon.parser import parser
from polyaxon.polyflow.builds import V1Build
from polyaxon.polyflow.cache import V1Cache
from polyaxon.polyflow.hooks import V1Hook
from polyaxon.polyflow.plugins import V1Plugins
from polyaxon.polyflow.termination import V1Termination
from polyaxon.schemas.base import NAME_REGEX, BaseSchemaModel
from polyaxon.schemas.fields.ref_or_obj import BoolOrRef, FloatOrRef, RefField


class BaseComponent(BaseSchemaModel):
    version: Optional[float]
    kind: Optional[StrictStr]
    name: Optional[Union[constr(regex=NAME_REGEX), RefField]]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    presets: Optional[List[StrictStr]]
    queue: Optional[StrictStr]
    cache: Optional[Union[V1Cache, RefField]]
    termination: Optional[Union[V1Termination, RefField]]
    plugins: Optional[Union[V1Plugins, RefField]]
    build: Optional[Union[V1Build, RefField]]
    hooks: Optional[Union[List[V1Hook], RefField]]
    is_approved: Optional[BoolOrRef] = Field(alias="isApproved")
    cost: Optional[FloatOrRef]

    @validator("tags", "presets", pre=True)
    def validate_str_list(cls, v, field):
        if isinstance(v, str):
            return parser.get_string(field, v, is_list=True)
        return v
