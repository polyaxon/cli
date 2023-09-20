from typing import Type

from clipped.formatting import Printer

from polyaxon._config.manager import ConfigManager
from polyaxon._sdk.schemas.v1_run import V1Run


class RunConfigManager(ConfigManager):
    """Manages run configuration .run file."""

    VISIBILITY = ConfigManager.Visibility.ALL
    IN_PROJECT_DIR = True
    CONFIG_FILE_NAME = ".run"
    CONFIG: Type[V1Run] = V1Run

    @classmethod
    def get_config_or_raise(cls) -> V1Run:
        run = cls.get_config()
        if not run:
            Printer.error("No run was provided.", sys_exit=True)

        return run
