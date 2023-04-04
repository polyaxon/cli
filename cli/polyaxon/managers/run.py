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

from polyaxon.managers.base import BaseConfigManager
from polyaxon.schemas.responses.v1_run import V1Run
from polyaxon.utils.formatting import Printer


class RunConfigManager(BaseConfigManager):
    """Manages run configuration .run file."""

    VISIBILITY = BaseConfigManager.VISIBILITY_ALL
    IN_POLYAXON_DIR = True
    CONFIG_FILE_NAME = ".run"
    CONFIG: Type[V1Run] = V1Run

    @classmethod
    def get_config_or_raise(cls) -> V1Run:
        run = cls.get_config()
        if not run:
            Printer.error("No run was provided.", sys_exit=True)

        return run
