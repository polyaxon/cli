from clipped.config.manager import ConfigManager as _ConfigManager

from polyaxon._config.reader import ConfigReader
from polyaxon._contexts import paths as ctx_paths
from polyaxon.logger import logger


class ConfigManager(_ConfigManager):
    _CONFIG_READER = ConfigReader
    _LOGGER = logger
    _PROJECT = ".polyaxon"
    _PROJECT_PATH: str = ctx_paths.CONTEXT_USER_POLYAXON_PATH
    _TEMP_PATH: str = ctx_paths.CONTEXT_TMP_POLYAXON_PATH
