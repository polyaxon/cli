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

from pydantic import StrictStr

from polyaxon import dist
from polyaxon.schemas.api.compatibility import V1Compatibility
from polyaxon.schemas.api.installation import V1Installation
from polyaxon.schemas.api.log_handler import V1LogHandler
from polyaxon.schemas.cli.checks_config import ChecksConfig


class CliConfig(ChecksConfig):
    _IDENTIFIER = "cli"
    _DIST = "dist"
    _INTERVAL = 30 * 60

    current_version: Optional[StrictStr]
    installation: Optional[V1Installation]
    compatibility: Optional[V1Compatibility]
    log_handler: Optional[V1LogHandler]

    @property
    def min_version(self) -> Optional[str]:
        if not self.compatibility or not self.compatibility.cli:
            return None
        return self.compatibility.cli.min

    @property
    def latest_version(self) -> Optional[str]:
        if not self.compatibility or not self.compatibility.cli:
            return None
        return self.compatibility.cli.latest

    @property
    def is_community(self) -> bool:
        return self.installation is None or dist.is_community(self.installation.dist)
