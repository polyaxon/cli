from typing import Type

from polyaxon._config.manager import ConfigManager
from polyaxon._flow import V1Init
from polyaxon._schemas.types import V1GitType


class GitConfigManager(ConfigManager):
    """Manages access token configuration .auth file."""

    VISIBILITY = ConfigManager.Visibility.LOCAL
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
