import os

from typing import Type

from polyaxon._config.manager import ConfigManager
from polyaxon._config.spec import ConfigSpec
from polyaxon._schemas.client import ClientConfig


class ClientConfigManager(ConfigManager):
    """Manages client configuration .client file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    CONFIG_FILE_NAME = ".client"
    CONFIG: Type[ClientConfig] = ClientConfig

    @classmethod
    def get_config_from_env(cls, **kwargs) -> ClientConfig:
        tmp_path = cls.get_tmp_config_path()
        glob_path = cls.get_global_config_path()

        config = cls._CONFIG_READER.read_configs(
            [
                ConfigSpec(tmp_path, config_type=".json", check_if_exists=False),
                ConfigSpec(glob_path, config_type=".json", check_if_exists=False),
                os.environ,
            ]
        )
        return ClientConfig.from_dict(config.data)
