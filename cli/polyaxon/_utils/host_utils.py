import os

from clipped.utils.http import clean_host

from polyaxon._env_vars.keys import ENV_KEYS_PLATFORM_HOST
from polyaxon.api import LOCALHOST


def get_api_host(default: str = LOCALHOST):
    return clean_host(os.environ.get(ENV_KEYS_PLATFORM_HOST, default))
