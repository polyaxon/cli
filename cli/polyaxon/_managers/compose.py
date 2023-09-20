from polyaxon._config.manager import ConfigManager


class ComposeConfigManager(ConfigManager):
    """Manages access cli configuration .compose file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    CONFIG_FILE_NAME = ".compose/.env"
    FREQUENCY = 3

    @classmethod
    def get_config_filepath(cls, create: bool = True) -> str:
        path = super().get_config_filepath(create=create)
        values = path.split("/")[:-1]
        cls._create_dir("/".join(values))
        return path
