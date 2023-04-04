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
from polyaxon.k8s.namespace import DEFAULT_NAMESPACE
from polyaxon.managers.base import BaseConfigManager, ManagerVisibility
from polyaxon.schemas.cli.agent_config import AgentConfig


class AgentConfigManager(BaseConfigManager):
    """Manages agent configuration .agent file."""

    VISIBILITY = ManagerVisibility.GLOBAL
    CONFIG_FILE_NAME = ".agent"
    CONFIG: Type[AgentConfig] = AgentConfig

    @classmethod
    def get_config_or_default(cls) -> AgentConfig:
        if not cls.is_initialized():
            return cls.CONFIG(
                namespace=DEFAULT_NAMESPACE, connections=[], secret_resources=[]
            )  # pylint:disable=not-callable

        return cls.get_config()

    @classmethod
    def get_config_from_env(cls) -> AgentConfig:
        tmp_path = cls.get_tmp_config_path()
        glob_path = cls.get_global_config_path()

        config_paths = [
            ConfigSpec(tmp_path, config_type=".json", check_if_exists=False),
            ConfigSpec(glob_path, config_type=".json", check_if_exists=False),
            os.environ,
            {"dummy": "dummy"},
        ]

        config = ConfigManager.read_configs(config_paths)
        return cls.CONFIG.from_dict(config.data)
