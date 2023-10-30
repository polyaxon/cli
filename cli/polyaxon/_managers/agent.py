import os

from typing import Type

from polyaxon._config.manager import ConfigManager
from polyaxon._config.spec import ConfigSpec
from polyaxon._k8s.namespace import DEFAULT_NAMESPACE
from polyaxon._schemas.agent import AgentConfig


class AgentConfigManager(ConfigManager):
    """Manages agent configuration .agent file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    CONFIG_FILE_NAME = ".agent"
    ALTERNATE_CONFIG_FILE_NAME = ".sandbox"
    CONFIG: Type[AgentConfig] = AgentConfig
    PERSIST_FORMAT = "yaml"

    @classmethod
    def get_config_or_default(cls) -> AgentConfig:
        if not cls.is_initialized():
            return cls.CONFIG(
                namespace=DEFAULT_NAMESPACE, connections=[], secret_resources=[]
            )  # pylint:disable=not-callable

        return cls.get_config()

    @classmethod
    def get_config_from_env(cls) -> AgentConfig:
        tmp_path = cls.get_tmp_config_path()
        glob_path = cls.get_global_config_path()

        config_paths = [
            ConfigSpec(tmp_path, config_type=".yaml", check_if_exists=False),
            ConfigSpec(glob_path, config_type=".yaml", check_if_exists=False),
            os.environ,
            {"dummy": "dummy"},
        ]

        config = cls._CONFIG_READER.read_configs(config_paths)
        return cls.CONFIG.from_dict(config.data)
