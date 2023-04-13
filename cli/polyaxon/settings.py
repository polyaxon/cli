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

from typing import TYPE_CHECKING, Optional

from clipped.formatting import Printer
from clipped.utils.bools import to_bool
from pydantic import ValidationError

from polyaxon.api import LOCALHOST
from polyaxon.env_vars.keys import EV_KEYS_NO_CONFIG, EV_KEYS_SET_AGENT
from polyaxon.managers.client import ClientConfigManager
from polyaxon.managers.home import HomeConfigManager
from polyaxon.managers.user import UserConfigManager
from polyaxon.services.values import PolyaxonServices

if TYPE_CHECKING:
    from polyaxon.deploy.schemas.auth import AccessTokenConfig
    from polyaxon.schemas.api.home import HomeConfig
    from polyaxon.schemas.cli.agent_config import AgentConfig
    from polyaxon.schemas.cli.cli_config import CliConfig
    from polyaxon.schemas.cli.client_config import ClientConfig

MIN_TIMEOUT = 1
LONG_REQUEST_TIMEOUT = 3600
HEALTH_CHECK_INTERVAL = 60

HOME_CONFIG: "HomeConfig" = HomeConfigManager.get_config_from_env()
AUTH_CONFIG: Optional["AccessTokenConfig"] = None
CLIENT_CONFIG: "ClientConfig"
CLI_CONFIG: Optional["CliConfig"] = None
AGENT_CONFIG: Optional["AgentConfig"] = None

PolyaxonServices.set_service_name()


def set_agent_config(config: Optional["AgentConfig"] = None):
    from polyaxon.managers.agent import AgentConfigManager

    global AGENT_CONFIG

    # Patch the config with correct home path if available
    AgentConfigManager.set_config_path(HOME_CONFIG.path)

    AGENT_CONFIG = config or AgentConfigManager.get_config_from_env()


def set_cli_config():
    from polyaxon.managers.cli import CliConfigManager

    global CLI_CONFIG

    # Patch the config with correct home path if available
    CliConfigManager.set_config_path(HOME_CONFIG.path)

    try:
        CLI_CONFIG = CliConfigManager.get_config_or_default()
    except (TypeError, ValidationError):
        CliConfigManager.purge()
        Printer.warning("Your CLI configuration was purged!")


def set_client_config():
    global CLIENT_CONFIG

    # Patch the config with correct home path if available
    ClientConfigManager.set_config_path(HOME_CONFIG.path)

    try:
        CLIENT_CONFIG = ClientConfigManager.get_config_from_env()
    except (TypeError, ValidationError):
        ClientConfigManager.purge()
        Printer.warning("Your client configuration was purged!")
        CLIENT_CONFIG = ClientConfigManager.get_config_from_env()


def set_auth_config():
    from polyaxon.managers.auth import AuthConfigManager

    global AUTH_CONFIG

    # Patch the config with correct home path if available
    AuthConfigManager.set_config_path(HOME_CONFIG.path)

    try:
        AUTH_CONFIG = AuthConfigManager.get_config_from_env()
    except (TypeError, ValidationError):
        AuthConfigManager.purge()
        Printer.warning("Your auth configuration was purged!")

    # Patch the config with correct home path if available
    UserConfigManager.set_config_path(HOME_CONFIG.path)

    try:
        UserConfigManager.get_config_or_default()
    except (TypeError, ValidationError):
        UserConfigManager.purge()
        Printer.warning("Your user configuration was purged!")


if not to_bool(os.environ.get(EV_KEYS_NO_CONFIG, False)):
    set_auth_config()
    set_client_config()
    if PolyaxonServices.is_agent() or to_bool(os.environ.get(EV_KEYS_SET_AGENT, False)):
        set_agent_config()
else:
    # Patch the config with correct home path if available
    ClientConfigManager.set_config_path(HOME_CONFIG.path)

    CLIENT_CONFIG = ClientConfigManager.CONFIG(host=LOCALHOST)
