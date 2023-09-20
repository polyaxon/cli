import os

from typing import Type

from polyaxon._config.manager import ConfigManager
from polyaxon._config.spec import ConfigSpec
from polyaxon._contexts import paths as ctx_paths
from polyaxon._schemas.authentication import AccessTokenConfig


class AuthConfigManager(ConfigManager):
    """Manages access token configuration .auth file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    CONFIG_FILE_NAME = ".auth"
    CONFIG: Type[AccessTokenConfig] = AccessTokenConfig

    @classmethod
    def get_config_from_env(cls) -> AccessTokenConfig:
        tmp_path = cls.get_tmp_config_path()
        user_path = cls.get_global_config_path()

        auth_config = cls._CONFIG_READER.read_configs(
            [
                ConfigSpec(tmp_path, config_type=".json", check_if_exists=False),
                ConfigSpec(user_path, config_type=".json", check_if_exists=False),
                os.environ,
                ConfigSpec(
                    ctx_paths.CONTEXT_MOUNT_AUTH,
                    config_type=".json",
                    check_if_exists=False,
                ),
                {"dummy": "dummy"},
            ]
        )
        return AccessTokenConfig.from_dict(auth_config.data)
