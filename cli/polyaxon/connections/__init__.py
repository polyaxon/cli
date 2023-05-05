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
from vents.config import AppConfig
from vents.settings import create_app

from polyaxon.config.parser import ConfigParser
from polyaxon.contexts import paths as ctx_paths
from polyaxon.exceptions import PolyaxonConnectionError
from polyaxon.logger import logger

CONNECTION_CONFIG = create_app(
    config=AppConfig(
        project_name="Polyaxon",
        project_url="https://polyaxon.com/",
        project_icon="https://cdn.polyaxon.com/static/v1/images/logo_small.png",
        env_prefix="POLYAXON",
        context_path=ctx_paths.CONTEXT_ROOT,
        logger=logger,
        exception=PolyaxonConnectionError,
        config_parser=ConfigParser,
    )
)

from polyaxon.connections.kinds import V1ConnectionKind
from polyaxon.connections.schemas import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionResource,
    V1GitConnection,
    V1HostConnection,
    V1HostPathConnection,
)
