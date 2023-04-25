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


from clipped.config.manager import ConfigManager as _ConfigManager

from polyaxon.config.reader import ConfigReader
from polyaxon.contexts import paths as ctx_paths
from polyaxon.logger import logger


class ConfigManager(_ConfigManager):
    _CONFIG_READER = ConfigReader
    _LOGGER = logger
    _PROJECT = ".polyaxon"
    _PROJECT_PATH: str = ctx_paths.CONTEXT_USER_POLYAXON_PATH
    _TEMP_PATH: str = ctx_paths.CONTEXT_TMP_POLYAXON_PATH
