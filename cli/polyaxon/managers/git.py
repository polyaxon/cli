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

from polyaxon.managers.base import BaseConfigManager, ManagerVisibility
from polyaxon.polyflow import V1Init
from polyaxon.schemas.types import V1GitType


class GitConfigManager(BaseConfigManager):
    """Manages access token configuration .auth file."""

    VISIBILITY = ManagerVisibility.LOCAL
    CONFIG_FILE_NAME = "polyaxongit.yaml"
    CONFIG: Type[V1Init] = V1Init

    @classmethod
    def get_config_from_env(cls) -> V1Init:
        pass

    @classmethod
    def get_config(cls, check: bool = True) -> V1Init:
        config = super(GitConfigManager, cls).get_config(check=check)
        if not config.git:
            config.git = V1GitType()

        return config
