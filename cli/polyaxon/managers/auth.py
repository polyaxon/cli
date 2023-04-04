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

from typing import Type

from polyaxon.config_reader.manager import ConfigManager
from polyaxon.config_reader.spec import ConfigSpec
from polyaxon.contexts import paths as ctx_paths
from polyaxon.managers.base import BaseConfigManager, ManagerVisibility
from polyaxon.schemas.api.authentication import AccessTokenConfig


class AuthConfigManager(BaseConfigManager):
    """Manages access token configuration .auth file."""

    VISIBILITY = ManagerVisibility.GLOBAL
    CONFIG_FILE_NAME = ".auth"
    CONFIG: Type[AccessTokenConfig] = AccessTokenConfig

    @classmethod
    def get_config_from_env(cls) -> AccessTokenConfig:
        tmp_path = cls.get_tmp_config_path()
        user_path = cls.get_global_config_path()

        auth_config = ConfigManager.read_configs(
            [
                ConfigSpec(tmp_path, config_type=".json", check_if_exists=False),
                ConfigSpec(user_path, config_type=".json", check_if_exists=False),
                os.environ,
                ConfigSpec(
                    ctx_paths.CONTEXT_MOUNT_AUTH,
                    config_type=".json",
                    check_if_exists=False,
                ),
                {"dummy": "dummy"},
            ]
        )
        return AccessTokenConfig.from_dict(auth_config.data)
