import sys

from typing import Type

from clipped.formatting import Printer

from polyaxon._config.manager import ConfigManager
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._utils import cli_constants


class ProjectConfigManager(ConfigManager):
    """Manages project configuration .project file."""

    VISIBILITY = ConfigManager.Visibility.ALL
    IN_PROJECT_DIR = True
    CONFIG_FILE_NAME = ".project"
    CONFIG: Type[V1Project] = V1Project

    @classmethod
    def get_config_or_raise(cls) -> V1Project:
        project = cls.get_config()
        if not project:
            Printer.error(
                "No project was found, please initialize a project."
                " {}".format(cli_constants.INIT_COMMAND)
            )
            sys.exit(1)

        return project
