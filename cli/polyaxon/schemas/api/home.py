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

from pydantic import Extra, Field, StrictStr

from polyaxon.env_vars.keys import EV_KEYS_HOME
from polyaxon.schemas.base import BaseSchemaModel


class HomeConfig(BaseSchemaModel):
    """
    Home config for managing Polyaxon's main context path.


    Args:
        path: `str`. The context path where to write/read configs.
    """

    _IDENTIFIER = "home"

    path: Optional[StrictStr] = Field(alias=EV_KEYS_HOME)

    class Config:
        extra = Extra.ignore
