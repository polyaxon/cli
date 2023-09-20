import datetime

from typing import TYPE_CHECKING, Optional, Type

from clipped.utils.tz import now

from polyaxon._config.manager import ConfigManager
from polyaxon._schemas.cli import CliConfig

if TYPE_CHECKING:
    from polyaxon._schemas.compatibility import V1Compatibility
    from polyaxon._schemas.installation import V1Installation
    from polyaxon._schemas.log_handler import V1LogHandler


class CliConfigManager(ConfigManager):
    """Manages access cli configuration .cli file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    CONFIG_FILE_NAME = ".cli"
    CONFIG: Type[CliConfig] = CliConfig

    @classmethod
    def reset(
        cls,
        current_version: Optional[str] = None,
        installation: Optional["V1Installation"] = None,
        compatibility: Optional["V1Compatibility"] = None,
        log_handler: Optional["V1LogHandler"] = None,
        last_check: Optional[datetime.datetime] = None,
    ) -> Optional[CliConfig]:
        if not any(
            [current_version, installation, compatibility, log_handler, last_check]
        ):
            return
        cli_config = cls.get_config_or_default()
        if current_version is not None:
            cli_config.current_version = current_version
        if installation is not None:
            cli_config.installation = installation
        if compatibility is not None:
            cli_config.compatibility = compatibility
        if log_handler is not None:
            cli_config.log_handler = log_handler
        if last_check is not None:
            cli_config.last_check = cli_config.get_last_check(last_check)

        CliConfigManager.set_config(config=cli_config)
        return cli_config

    @classmethod
    def should_check(cls, interval: Optional[int] = None) -> bool:
        config = cls.get_config_or_default()
        should_check = config.should_check(interval=interval)
        if should_check:
            cls.reset(last_check=now())
        return should_check

    @classmethod
    def get_config_from_env(cls) -> Optional[CliConfig]:
        pass
