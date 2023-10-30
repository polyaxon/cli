import os

from typing import Optional

from clipped.compact.pydantic import ValidationError
from clipped.formatting import Printer
from clipped.utils.bools import to_bool

from polyaxon._env_vars.keys import ENV_KEYS_NO_CONFIG, ENV_KEYS_SET_AGENT
from polyaxon._managers.client import ClientConfigManager
from polyaxon._managers.home import HomeConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._schemas.agent import AgentConfig
from polyaxon._schemas.authentication import AccessTokenConfig
from polyaxon._schemas.cli import CliConfig
from polyaxon._schemas.client import ClientConfig
from polyaxon._schemas.home import HomeConfig
from polyaxon._services.values import PolyaxonServices
from polyaxon.api import LOCALHOST

from polyaxon._managers.ignore import IgnoreConfigManager  # noqa
from polyaxon._managers.run import RunConfigManager  # noqa
from polyaxon._managers.project import ProjectConfigManager  # noqa
from polyaxon._managers.auth import AuthConfigManager  # noqa
from polyaxon._managers.cli import CliConfigManager  # noqa

MIN_TIMEOUT = 1
LONG_REQUEST_TIMEOUT = 3600
HEALTH_CHECK_INTERVAL = 60
SET_AGENT = to_bool(os.environ.get(ENV_KEYS_SET_AGENT, False))

HOME_CONFIG: HomeConfig = HomeConfigManager.get_config_from_env()
AUTH_CONFIG: Optional[AccessTokenConfig] = None
CLIENT_CONFIG: ClientConfig
CLI_CONFIG: Optional[CliConfig] = None
AGENT_CONFIG: Optional[AgentConfig] = None

PolyaxonServices.set_service_name()


def set_home_config(config: Optional[HomeConfig] = None):
    global HOME_CONFIG

    HOME_CONFIG = config or HomeConfigManager.get_config_from_env()


def set_agent_config(config: Optional[AgentConfig] = None):
    from polyaxon._connections import CONNECTION_CONFIG
    from polyaxon._managers.agent import AgentConfigManager

    global AGENT_CONFIG

    # Patch the config with correct home path if available
    AgentConfigManager.set_config_path(HOME_CONFIG.path)

    AGENT_CONFIG = config or AgentConfigManager.get_config_from_env()

    # Set artifacts store name
    AGENT_CONFIG.set_artifacts_store_name()

    # Always sync the connections catalog to the current agent config
    CONNECTION_CONFIG.set_connections_catalog(AGENT_CONFIG.all_connections)


def set_cli_config():
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


if not to_bool(os.environ.get(ENV_KEYS_NO_CONFIG, False)):
    set_auth_config()
    set_client_config()
    if PolyaxonServices.is_agent() or SET_AGENT:
        set_agent_config()
else:
    # Patch the config with correct home path if available
    ClientConfigManager.set_config_path(HOME_CONFIG.path)

    CLIENT_CONFIG = ClientConfigManager.CONFIG(host=LOCALHOST)
