import os

from typing import Dict, Type

from polyaxon._config.manager import ConfigManager
from polyaxon._config.spec import ConfigSpec
from polyaxon._schemas.home import HomeConfig


class HomeConfigManager(ConfigManager):
    """Manages home configuration .home file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    CONFIG_FILE_NAME = ".home"
    CONFIG: Type[HomeConfig] = HomeConfig
    PERSIST_FORMAT = "yaml"

    @classmethod
    def get_config_defaults(cls) -> Dict[str, str]:
        return {"path": cls.get_global_config_path()}

    @classmethod
    def get_config_from_env(cls) -> HomeConfig:
        glob_path = cls.get_global_config_path()
        home_config = cls._CONFIG_READER.read_configs(
            [
                ConfigSpec(glob_path, config_type=".yaml", check_if_exists=False),
                os.environ,
                {"dummy": "dummy"},
            ]
        )
        return HomeConfig.from_dict(home_config.data)
