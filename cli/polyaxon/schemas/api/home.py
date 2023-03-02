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

from marshmallow import fields

from polyaxon.env_vars.keys import EV_KEYS_HOME
from polyaxon.schemas.base import BaseConfig, BaseSchema


class HomeSchema(BaseSchema):
    path = fields.Str(data_key=EV_KEYS_HOME)

    @staticmethod
    def schema_config():
        return HomeConfig


class HomeConfig(BaseConfig):
    """
    Home config for managing Polyaxon's main context path.


    Args:
        path: `str`. The context path where to write/read configs.
    """

    SCHEMA = HomeSchema
    IDENTIFIER = "home"

    def __init__(self, path=None):
        self.path = path
