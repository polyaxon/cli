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
import os

from typing import Dict, Type

from polyaxon.config_reader.manager import ConfigManager
from polyaxon.config_reader.spec import ConfigSpec
from polyaxon.managers.base import BaseConfigManager, ManagerVisibility
from polyaxon.schemas.api.home import HomeConfig


class HomeConfigManager(BaseConfigManager):
    """Manages home configuration .home file."""

    VISIBILITY = ManagerVisibility.GLOBAL
    CONFIG_FILE_NAME = ".home"
    CONFIG: Type[HomeConfig] = HomeConfig

    @classmethod
    def get_config_defaults(cls) -> Dict[str, str]:
        return {"path": cls.get_global_config_path()}

    @classmethod
    def get_config_from_env(cls) -> HomeConfig:
        glob_path = cls.get_global_config_path()
        home_config = ConfigManager.read_configs(
            [
                ConfigSpec(glob_path, config_type=".json", check_if_exists=False),
                os.environ,
                {"dummy": "dummy"},
            ]
        )
        return HomeConfig.from_dict(home_config.data)
