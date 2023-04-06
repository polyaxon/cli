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
from typing import Type

from clipped.formatting import Printer

from polyaxon.managers.base import BaseConfigManager, ManagerVisibility
from polyaxon.schemas.responses.v1_user import V1User


class UserConfigManager(BaseConfigManager):
    """Manages user configuration .user file."""

    VISIBILITY = ManagerVisibility.GLOBAL
    IN_POLYAXON_DIR = True
    CONFIG_FILE_NAME = ".user"
    CONFIG: Type[V1User] = V1User

    @classmethod
    def get_config_or_raise(cls) -> V1User:
        user = cls.get_config()
        if not user:
            Printer.error("User configuration was not found.", sys_exit=True)

        return user

    @classmethod
    def get_config_from_env(cls):
        pass
