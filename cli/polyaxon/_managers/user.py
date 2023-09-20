from typing import Type

from clipped.formatting import Printer

from polyaxon._config.manager import ConfigManager
from polyaxon._sdk.schemas.v1_user import V1User


class UserConfigManager(ConfigManager):
    """Manages user configuration .user file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    IN_PROJECT_DIR = True
    CONFIG_FILE_NAME = ".user"
    CONFIG: Type[V1User] = V1User

    @classmethod
    def get_config_or_raise(cls) -> V1User:
        user = cls.get_config()
        if not user:
            Printer.error("User configuration was not found.", sys_exit=True)

        return user

    @classmethod
    def get_config_from_env(cls):
        pass
